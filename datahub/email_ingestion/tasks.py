from celery import shared_task
from celery.utils.log import get_task_logger

from datahub.core.task_utils import acquire_lock
from datahub.email_ingestion.mailbox import mailbox_manager

logger = get_task_logger(__name__)


@shared_task(acks_late=True, priority=9)
def ingest_emails():
    """
    Ingest and process new emails for all mailboxes in the application - i.e.
    those in the MAILBOXES django setting.
    """
    expire_seconds = 60 * 10  # 10 minutes
    # Acquire a processing lock for 10 minutes - this will ensure that multiple
    # ingestion workers do not run at the same time and therefore prevent the
    # chance of messages being processed more than once
    with acquire_lock('ingest_emails', expire_seconds) as acquired:
        if not acquired:
            logger.info('Emails are already being ingested by another worker')
            return
        for mailbox in mailbox_manager.get_all_mailboxes():
            mailbox.process_new_mail()
