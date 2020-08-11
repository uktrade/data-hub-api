import requests
from celery import shared_task

from datahub.company import consent


@shared_task(
    max_retries=5,
    autoretry_for=(requests.exceptions.RequestException,),
    retry_backoff=30,
)
def update_contact_consent(email_address, accepts_dit_email_marketing, modified_at=None):
    """
    Update consent preferences.
    """
    consent.update_consent(
        email_address,
        accepts_dit_email_marketing,
        modified_at=modified_at,
    )
