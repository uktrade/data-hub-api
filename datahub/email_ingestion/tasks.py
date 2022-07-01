from celery import shared_task
from celery.utils.log import get_task_logger

from datahub.core.cache import skip_if_running
from datahub.email_ingestion import emails, mailbox_handler
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.interaction import (
    INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME,
    MAILBOX_INGESTION_FEATURE_FLAG_NAME,
)

logger = get_task_logger(__name__)


@shared_task(acks_late=True, priority=9)
@skip_if_running(busy_message='Emails are already being ingested by another worker')
def ingest_emails():
    """
    Ingest and process new emails for all mailboxes in the application - i.e.
    those in the MAILBOXES django setting.
    """
    # NOTE: This is a long-lived feature flag which allows us to quickly switch off email
    # ingestion in case of any problems with third party (SMTP) services or security issues
    if not is_feature_flag_active(INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        return
    for mailbox in mailbox_handler.get_all_mailboxes():
        mailbox.process_new_mail()


@shared_task(acks_late=True, priority=9)
@skip_if_running(busy_message='Emails are already being processed by another worker')
def process_mailbox_emails():
    """
    Process new emails for S3 mailboxes.
    """
    # NOTE: This is a long-lived feature flag which allows us to quickly switch off email
    # ingestion in case of any problems with third party (SMTP) services or security issues
    if not is_feature_flag_active(MAILBOX_INGESTION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{MAILBOX_INGESTION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        logger.info('Processing ingestion emails')
        emails.process_ingestion_emails()
