import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django_pglocks import advisory_lock

from datahub.company import consent
from datahub.company.models import Contact
from datahub.core.realtime_messaging import send_realtime_message

logger = get_task_logger(__name__)


def _automatic_contact_archive(limit=1000, simulate=False):
    contacts_to_be_archived = Contact.objects.filter(
        archived=False, company__archived=True,
    ).prefetch_related('company')[:limit]

    for contact in contacts_to_be_archived:
        message = f'Automatically archived contact: {contact.id}'
        if simulate:
            logger.info(f'[SIMULATION] {message}')
            continue
        contact.archived = True
        contact.archived_reason = f'Record was automatically archived due to the company ' \
                                  f'"{contact.company.name}" being archived'
        contact.archived_on = timezone.now()
        contact.save(
            update_fields=[
                'archived',
                'archived_reason',
                'archived_on',
            ],
        )
        logger.info(message)

    return contacts_to_be_archived.count()


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


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    max_retries=3,
    queue='long-running',
    # name set explicitly to maintain backwards compatibility
    name='datahub.company.tasks.automatic_contact_archive',
)
def automatic_contact_archive(self, limit=1000, simulate=False):
    """
    Archive inactive contacts.
    """
    with advisory_lock('automatic_contact_archive', wait=False) as acquired:

        if not acquired:
            logger.info('Another instance of this task is already running.')
            return

        archive_count = _automatic_contact_archive(limit=limit, simulate=simulate)
        realtime_message = f'{self.name} archived: {archive_count}'
        send_realtime_message(realtime_message)
