import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests_hawk import HawkAuth

from datahub.company.constants import (
    CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
    UPDATE_CONSENT_SERVICE_FEATURE_FLAG,
)
from datahub.core.api_client import APIClient
from datahub.feature_flag.utils import is_feature_flag_active

logger = get_task_logger(__name__)

CONSENT_SERVICE_PERSON_PATH = 'api/v1/person/'


def _update_contact_consent(email_address, accepts_dit_email_marketing, modified_at=None):
    if not all([
        settings.CONSENT_SERVICE_HAWK_ID,
        settings.CONSENT_SERVICE_HAWK_KEY,
        settings.CONSENT_SERVICE_BASE_URL,
    ]):
        raise ImproperlyConfigured(
            'The all CONSENT_SERVICE_* settings must be set to use this task.')
    # once feature flag is remove this can be moved to be a module level constant.
    auth = HawkAuth(
        id=settings.CONSENT_SERVICE_HAWK_ID,
        key=settings.CONSENT_SERVICE_HAWK_KEY,
    )

    body = {
        'consents': [CONSENT_SERVICE_EMAIL_CONSENT_TYPE] if accepts_dit_email_marketing else [],
        'email': email_address,
    }

    if modified_at:
        body['modified_at'] = modified_at.isoformat()

    connect_timeout, read_timeout = 5.0, 30.0
    api_client = APIClient(
        settings.CONSENT_SERVICE_BASE_URL,
        auth=auth,
        default_timeout=(connect_timeout, read_timeout),
    )

    response = api_client.request(
        'post',
        CONSENT_SERVICE_PERSON_PATH,
        json=body,
    )
    logger.debug(response.json())


@shared_task(
    max_retries=5,
    autoretry_for=(requests.exceptions.RequestException,),
    retry_backoff=30,
)
def update_contact_consent(email_address, accepts_dit_email_marketing, modified_at=None):
    """
    Archive inactive companies.
    """
    if not is_feature_flag_active(UPDATE_CONSENT_SERVICE_FEATURE_FLAG):
        logger.info(
            f'Feature flag "{UPDATE_CONSENT_SERVICE_FEATURE_FLAG}" is not active, exiting.',
        )
        return
    _update_contact_consent(email_address, accepts_dit_email_marketing, modified_at=modified_at)
