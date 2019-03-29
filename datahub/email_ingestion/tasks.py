from celery import shared_task
from celery.utils.log import get_task_logger

from datahub.email_ingestion.mailbox import mailbox_manager
from datahub.core.task_utils import acquire_lock

logger = get_task_logger(__name__)


@shared_task(acks_late=True, priority=9)
def ingest_emails():
    """
    """
    expire_seconds = 60 * 10  # 10 minutes
    with acquire_lock("ingest_emails", expire_seconds) as acquired:
        if not acquired:
            logger.info("Emails are already being ingested by another worker")
            return
        for mailbox in mailbox_manager.get_all_mailboxes():
            mailbox.process_new_mail()
