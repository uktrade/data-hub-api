from celery import shared_task
from celery.utils.log import get_task_logger
from django_mailbox.models import Mailbox

from datahub.core.task_utils import acquire_lock

logger = get_task_logger(__name__)


@shared_task(acks_late=True, priority=9)
def ingest_emails():
    """
    """
    expire_seconds = 60 * 10  # 10 minutes
    with acquire_lock("ingest_emails", expire_seconds) as acquired:
        if acquired:
            mailboxes = Mailbox.objects.filter(active=True)
            for mailbox in mailboxes:
                mailbox.get_new_mail()
        else:
            logger.info("Emails are already being ingested by another worker")
