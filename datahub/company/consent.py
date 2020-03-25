"""
A wrapper around the DIT Legal Basis service which allows for both querying
and setting email marketing consent for an email address.
"""

import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from datahub.company.constants import CONSENT_SERVICE_EMAIL_CONSENT_TYPE
from datahub.core.api_client import APIClient, HawkAuth

logger = logging.getLogger(__name__)

CONSENT_SERVICE_PERSON_PATH = 'api/v1/person/'
CONSENT_SERVICE_PERSON_PATH_LOOKUP = f'{CONSENT_SERVICE_PERSON_PATH}bulk_lookup/'
CONSENT_SERVICE_CONNECT_TIMEOUT = 5.0
CONSENT_SERVICE_READ_TIMEOUT = 30.0


def _get_client():
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
        verify_response=settings.CONSENT_SERVICE_HAWK_VERIFY_RESPONSE,
    )

    _api_client = APIClient(
        settings.CONSENT_SERVICE_BASE_URL,
        auth=_auth,
        default_timeout=(CONSENT_SERVICE_CONNECT_TIMEOUT, CONSENT_SERVICE_READ_TIMEOUT),
    )
    return _api_client


def update_consent(email_address, accepts_dit_email_marketing, modified_at=None):
    """
    Update marketing consent for an email address
    :param email_address: email address you want to update marketing consent for
    :param accepts_dit_email_marketing: True if they want marketing, False if they don't
    :param modified_at: iso8601 formatted datetime with timezone, in UTC as a string
    """
    logger.info(f'update_consent: {email_address}, {accepts_dit_email_marketing}')

    body = {
        'consents': [
            CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
        ] if accepts_dit_email_marketing else [],
        'email': email_address,
    }

    if modified_at:
        body['modified_at'] = modified_at

    _get_client().request(
        'post',
        CONSENT_SERVICE_PERSON_PATH,
        json=body,
    )


def get_many(emails):
    """
    Bulk lookup consent for a list of emails

    :param emails: List of email addresses
    :return: dict of email address to consent status
    """
    body = {
        'emails': emails,
    }

    response = _get_client().request(
        'POST',
        CONSENT_SERVICE_PERSON_PATH_LOOKUP,
        json=body,
        params={'limit': len(emails)},
    )
    return {
        result['email']: CONSENT_SERVICE_EMAIL_CONSENT_TYPE in result['consents']
        for result in response.json()['results']
    }


def get_one(email):
    """
    Get consent for single email address
    :return: bool indicating if we have consent to send email marketing
    to an address
    """
    return get_many([email]).get(email, False)
