from logging import getLogger
from urllib.parse import urljoin

import requests


logger = getLogger(__name__)


class APIClient:
    """Generic API client."""

    # Prefer JSON to other content types
    DEFAULT_ACCEPT = 'application/json;q=0.9,*/*;q=0.8'

    def __init__(self, api_url, auth=None, accept=DEFAULT_ACCEPT, default_timeout=None):
        """Initialises the API client."""
        self._api_url = api_url
        self._auth = auth
        self._accept = accept
        self._default_timeout = default_timeout

    def request(self, method, path, **kwargs):
        """Makes an HTTP request."""
        url = urljoin(self._api_url, path)
        logger.info(f'Sending request: {method.upper()} {url}')

        timeout = kwargs.pop('timeout', self._default_timeout)

        headers = {}
        if self._accept:
            headers['Accept'] = self._accept

        response = requests.request(
            method, url, auth=self._auth, headers=headers, timeout=timeout, **kwargs
        )
        logger.info(f'Response received: {response.status_code} {method.upper()} {url}')
        response.raise_for_status()
        return response
