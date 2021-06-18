from logging import getLogger
from urllib.parse import urljoin, urlparse

import requests
from mohawk import Sender
from requests.auth import AuthBase
from requests.exceptions import ConnectionError

from datahub.core.exceptions import APIBadGatewayException

logger = getLogger(__name__)


class HawkAuth(AuthBase):
    """Hawk authentication class."""

    def __init__(self, api_id, api_key, signing_algorithm='sha256', verify_response=True):
        """Initialises the authenticator with the signing parameters."""
        self._api_id = api_id
        self._api_key = api_key
        self._signing_algorithm = signing_algorithm
        self._verify_response = verify_response

    def __call__(self, request):
        """Signs a request, and attaches a response verifier."""
        credentials = {
            'id': self._api_id,
            'key': self._api_key,
            'algorithm': self._signing_algorithm,
        }

        sender = Sender(
            credentials,
            request.url,
            request.method,
            content=request.body or '',
            content_type=request.headers.get('Content-Type', ''),
        )

        request.headers['Authorization'] = sender.request_header
        if self._verify_response:
            request.register_hook('response', _make_response_verifier(sender))

        return request


class TokenAuth(AuthBase):
    """
    Token authentication class.
    """

    def __init__(self, token, token_keyword='Token'):
        """
        Initialise the class with the token.
        """
        self.token = token
        self.token_keyword = token_keyword

    def __call__(self, request):
        """
        Inject the Authorization header in to the request.
        """
        request.headers['Authorization'] = f'{self.token_keyword} {self.token}'
        return request


def _make_response_verifier(sender):
    def verify_response(response, *args, **kwargs):
        if response.ok:
            sender.accept_response(
                response.headers['Server-Authorization'],
                content=response.content,
                content_type=response.headers['Content-Type'],
            )

    return verify_response


class APIClient:
    """Generic API client."""

    # Prefer JSON to other content types
    DEFAULT_ACCEPT = 'application/json;q=0.9,*/*;q=0.8'

    def __init__(
        self,
        api_url,
        auth=None,
        accept=DEFAULT_ACCEPT,
        default_timeout=None,
        raise_for_status=True,
        request=None,
    ):
        """Initialises the API client."""
        self._api_url = api_url
        self._auth = auth
        self._accept = accept
        self._default_timeout = default_timeout
        self._raise_for_status = raise_for_status
        self._request = request

    def request(self, method, path, **kwargs):
        """Makes an HTTP request."""
        url = urljoin(self._api_url, path)

        logger.info(f'Sending request: {method.upper()} {url}')

        timeout = kwargs.pop('timeout', self._default_timeout)

        headers = kwargs.pop('headers', {})
        if self._accept:
            headers['Accept'] = self._accept
        if self._request:
            headers.update(get_zipkin_headers(self._request))

        try:
            response = requests.request(
                method,
                url,
                auth=self._auth,
                headers=headers,
                timeout=timeout,
                **kwargs,
            )
        except ConnectionError as e:
            logger.exception(e)
            raise APIBadGatewayException(
                f'Upstream service unavailable: {urlparse(url).netloc}',
            ) from e
        logger.info(f'Response received: {response.status_code} {method.upper()} {url}')
        if self._raise_for_status:
            response.raise_for_status()
        return response


def get_zipkin_headers(request):
    """
    Parsers the request object and extracts Zipkin headers.

    :param request: The request object
    """
    if not request:
        return {}

    keys = [
        'x-b3-traceid',
        'x-b3-spanid',
    ]
    headers = {
        key: request.headers.get(key)
        for key in keys if key in request.headers
    }
    return headers
