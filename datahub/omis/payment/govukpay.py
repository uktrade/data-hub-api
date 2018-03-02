import urllib.parse
from logging import getLogger

import requests
from django.conf import settings
from django.utils.functional import cached_property
from rest_framework.exceptions import APIException


logger = getLogger(__name__)


class GOVUKPayAPIException(APIException):
    """GOV.UK Pay generic exception."""

    def __init__(self, *args, response=None, **kwargs):
        """Keep a copy of the response."""
        super().__init__(*args, **kwargs)
        self.response = response


def govuk_url(path):
    """
    :returns: url to the GOV.UK Pay endpoint defined by `path`

    :param path: path without leading `/` e.g. `payments`
    """
    return urllib.parse.urljoin(settings.GOVUK_PAY_URL, path)


class PayClient:
    """Client used to interface with GOV.UK Pay."""

    @cached_property
    def _headers(self):
        """GOV.UK common headers including the Authorization one."""
        return {
            'Accept': 'application/json',
            'Authorization': f'Bearer {settings.GOVUK_PAY_AUTH_TOKEN}'
        }

    def _raise_for_status(self, response):
        """
        :raises GOVUKPayAPIException if status code >= 400

        :param response: Response instance to check
        """
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise GOVUKPayAPIException(exc) from exc

    def _request(self, method, path, **kwargs):
        """
        :return: response instance
        :raises GOVUKPayAPIException if status code >= 400

        :param method: HTTP verb (e.g. 'GET')
        :param path: relative path to the GOV.UK endpoint (e.g. 'payments')
        :param **kwargs: any other param to be passed to the request method
            exactly as they are.
            The headers and timeout values are set automatically but can be
            overridden by kwargs if needed.
        """
        request_kwargs = {
            'headers': self._headers,
            'timeout': settings.GOVUK_PAY_TIMEOUT,
            **kwargs
        }
        url = govuk_url(path)

        logger.info(f'GOV.UK Pay - {method} call for url {url} - Preparing')
        response = requests.request(method, url, **request_kwargs)
        logger.info(
            f'GOV.UK Pay - {method} call for url {url} '
            f'- DONE - status code {response.status_code}'
        )

        self._raise_for_status(response)
        return response

    def create_payment(self, amount, reference, description, return_url):
        """
        Create a new payment.

        :returns: dictionary with the created payment data
        :raises: GOVUKPayAPIException if status code >= 400

        :param amount: amount in pence
        :param reference: payment reference
        :param description: payment description
        :param return_url: service return url
        """
        return self._request(
            'POST',
            path='payments',
            json={
                'amount': amount,
                'reference': reference,
                'description': description,
                'return_url': return_url,
            }
        ).json()

    def get_payment_by_id(self, payment_id):
        """
        :returns: dictionary with the payment data for object with id == `payment_id`
        :raises: GOVUKPayAPIException if status code >= 400

        :param payment_id: id of the GOV.UK payment
        """
        return self._request('GET', path=f'payments/{payment_id}').json()

    def cancel_payment(self, payment_id):
        """
        Cancel a payment.

        :returns: always None
        :raises: GOVUKPayAPIException if status code >= 400

        :param payment_id: id of the GOV.UK payment
        """
        self._request('POST', path=f'payments/{payment_id}/cancel')
