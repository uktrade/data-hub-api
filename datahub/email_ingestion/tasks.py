from logging import getLogger

from django_pglocks import advisory_lock

from datahub.email_ingestion import emails
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.interaction import MAILBOX_INGESTION_FEATURE_FLAG_NAME

logger = getLogger(__name__)


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
        return
    # Acquire a processing lock for the duration of the current DB session -
    # this will ensure that multiple ingestion workers do not run at the same
    # time and therefore prevent the chance of messages being processed more
    # than once
    with advisory_lock('process_mailbox_emails', wait=False) as acquired:
        if not acquired:
            logger.info('Emails are already being processed by another worker')
            return
        emails.process_ingestion_emails()
