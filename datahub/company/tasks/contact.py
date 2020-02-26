import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from datahub.company import consent
from datahub.company.constants import (
    UPDATE_CONSENT_SERVICE_FEATURE_FLAG,
)
from datahub.feature_flag.utils import is_feature_flag_active

logger = get_task_logger(__name__)


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
    consent.update_consent(
        email_address,
        accepts_dit_email_marketing,
        modified_at=modified_at,
    )
