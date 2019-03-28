from celery import shared_task
from celery.utils.log import get_task_logger

from datahub.email_ingestion.mailbox import mailboxes
from datahub.email_ingestion.email_processor_manager import processor_manager
from datahub.core.task_utils import acquire_lock

logger = get_task_logger(__name__)


def _process_email(message):
    logger.info("Attachments:")
    logger.info(message.attachments)
    logger.info("Headers:")
    logger.info(message._message.keys())
    logger.info(dir(message))
    logger.info("Subject: %s" % message.subject)
    logger.info("To: %s" % message.to)
    logger.info("From: %s" % message.from_)
    logger.info("CC: %s" % message.cc)
    logger.info("Authentication: %s" % message.authentication_results)
    logger.info("Text-plain:")
    logger.info(message.text_plain)
    logger.info("Text-html:")
    logger.info(message.text_html)
    processor_manager.process_email(message)


def _process_all_emails():
    for mailbox in mailboxes.get_all_mailboxes():
        messages = mailbox.get_new_mail()
        for message in messages:
            _process_email(message)


@shared_task(acks_late=True, priority=9)
def ingest_emails():
    """
    """
    expire_seconds = 60 * 10  # 10 minutes
    with acquire_lock("ingest_emails", expire_seconds) as acquired:
        if not acquired:
            logger.info("Emails are already being ingested by another worker")
            return
        _process_all_emails()
