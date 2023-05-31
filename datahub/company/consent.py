"""
A wrapper around the DIT Legal Basis service which allows for both querying
and setting email marketing consent for an email address.
"""

import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests.exceptions import HTTPError, Timeout

from datahub.company.constants import CONSENT_SERVICE_EMAIL_CONSENT_TYPE
from datahub.core.api_client import APIClient, HawkAuth
from datahub.core.exceptions import APIBadGatewayException

logger = logging.getLogger(__name__)

CONSENT_SERVICE_PERSON_PATH = 'api/v1/person/'
CONSENT_SERVICE_PERSON_PATH_LOOKUP = f'{CONSENT_SERVICE_PERSON_PATH}bulk_lookup/'
CONSENT_SERVICE_CONNECT_TIMEOUT = 5.0
CONSENT_SERVICE_READ_TIMEOUT = 30.0


class ConsentAPIError(Exception):
    """
    Base exception class for Consent API related errors.
    """


class ConsentAPIHTTPError(ConsentAPIError):
    """
    Exception for all HTTP errors.
    """


class ConsentAPITimeoutError(ConsentAPIError):
    """
    Exception for when a timeout was encountered when connecting to Consent API.
    """


class ConsentAPIConnectionError(ConsentAPIError):
    """
    Exception for when an error was encountered when connecting to Consent API.
    """


class CaseInsensitiveDict(dict):
    """Inherit dict class to make keys case insitive."""

    def __setitem__(self, key, value):
        """Transform key to lower case when setting an item."""
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key):
        """Transform key to lower case when getting an item."""
        return super().__getitem__(key.lower())

    def get(self, key, default=False):
        """Transform key to lower case when getting an item using a dict get method."""
        return super().get(key.lower(), default)


def _get_client(request=None):
    """
    Get configured API client for the consent service,
    _api_client could've just been set as a top level attribute
    of this module but that makes testing harder as the settings are
    loaded at `import` time rather than at run time. Which breaks test
    utilities like Django's override_settings decorator which is used
    to change django settings inside tests.
    """
    if not all([
        settings.CONSENT_SERVICE_HAWK_ID,
        settings.CONSENT_SERVICE_HAWK_KEY,
        settings.CONSENT_SERVICE_BASE_URL,
    ]):
        raise ImproperlyConfigured(
            'CONSENT_SERVICE_* environment variables must be set, see README',
        )

    _auth = HawkAuth(
        api_id=settings.CONSENT_SERVICE_HAWK_ID,
        api_key=settings.CONSENT_SERVICE_HAWK_KEY,
    )

    _api_client = APIClient(
        settings.CONSENT_SERVICE_BASE_URL,
        auth=_auth,
        default_timeout=(CONSENT_SERVICE_CONNECT_TIMEOUT, CONSENT_SERVICE_READ_TIMEOUT),
        request=request,
    )
    return _api_client


def update_consent(email_address, accepts_dit_email_marketing, modified_at=None,
                   **kwargs):
    """
    Update marketing consent for an email address
    :param email_address: email address you want to update marketing consent for
    :param accepts_dit_email_marketing: True if they want marketing, False if they don't
    :param modified_at: iso8601 formatted datetime with timezone, in UTC as a string
    """
    if (email_address is None or len(str(email_address).strip()) == 0):
        raise ValueError('email_address is a required field')

    logger.info(f'update_consent: {email_address}, {accepts_dit_email_marketing}')

    body = {
        'consents': [
            CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
        ] if accepts_dit_email_marketing else [],
        'email': email_address.lower(),
    }

    if modified_at:
        body['modified_at'] = modified_at

    headers = {
        **kwargs.get('headers', {}),
        **kwargs.get('zipkin_headers', {}),
    }

    _get_client().request(
        'post',
        CONSENT_SERVICE_PERSON_PATH,
        json=body,
        headers=headers,
    )


def get_many(emails):
    """
    Bulk lookup consent for a list of emails
    :param emails: List of email addresses
    :return: dict of email address to consent status

    Below is a sample of the data shape.
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1486081,
                "consents": [
                    "email_marketing"
                ],
                "modified_at": "2020-07-27T11:54:51.796358Z",
                "key": "",
                "email": "example@example.com",
                "phone": "",
                "key_type": "email",
                "created_at": "2020-07-27T11:54:51.874350Z",
                "current": true
                }
            ]
        }
    }
    """
    api_client = _get_client()

    try:
        response = api_client.request(
            'GET',
            CONSENT_SERVICE_PERSON_PATH_LOOKUP,
            params={'email': [email.lower() for email in emails]},
        )
    except APIBadGatewayException as exc:
        logger.error(exc)
        error_message = 'Encountered an error connecting to Legal Basis API'
        raise ConsentAPIConnectionError(error_message) from exc
    except Timeout as exc:
        logger.error(exc)
        error_message = 'Encountered a timeout interacting with Legal Basis API'
        raise ConsentAPITimeoutError(error_message) from exc
    except HTTPError as exc:
        logger.error(exc)
        error_message = (
            'The Legal Basis API returned an error status: '
            f'{exc.response.status_code}',
        )
        raise ConsentAPIHTTPError(error_message) from exc

    results = {
        result['email']: CONSENT_SERVICE_EMAIL_CONSENT_TYPE in result['consents']
        for result in response.json()['results']
    }
    return CaseInsensitiveDict(results)


def get_one(email):
    """
    Get consent for single email address
    :return: bool indicating if we have consent to send email marketing
    to an address
    """
    return get_many([email]).get(email, False)
