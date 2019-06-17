from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django_pglocks import advisory_lock

from datahub.email_ingestion import mailbox_handler
from datahub.email_ingestion.mailbox import EmailInboxConnectionError
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.interaction import INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME

logger = get_task_logger(__name__)


def handle_connection_error(exc, mailbox_identifier):
    """
    Handles an EmailInboxConnectionError exception which has been raised when connecting to an
    email inbox.  This will keep a count of the number of failures within the last 10
    attempts and will raise an EmailInboxConnectionError exception if the number
    of failures has exceeded the EMAIL_INGESTION_CONNECT_FAILURE_THRESHOLD setting.

    This will only raise one exception each time that the number of connection errors
    exceeds EMAIL_INGESTION_CONNECT_FAILURE_THRESHOLD within the 10 attempt window.
    e.g. If we have a threshold of 5, one exception will be raised to represent
    the first 5 failures and a second exception will only be raised after another
    subsequent 5 failures. This stops the exceptions from being too noisy.
    """
    email_ingest_failures_key = f'email_ingest_failures_{mailbox_identifier}'
    window_size = 10
    try:
        failures = cache.incr(email_ingest_failures_key)
    except ValueError:
        # We are not tracking failures for the current window, so we need to add a new cache entry
        failures = 1
        failure_window = int(settings.EMAIL_INGESTION_FREQUENCY_SECONDS) * window_size
        cache.set(email_ingest_failures_key, failures, failure_window)

    if failures >= settings.EMAIL_INGESTION_CONNECT_FAILURE_THRESHOLD:
        # Delete the failure tracker cache entry - so that we need to hit the threshold
        # again before raising the next error
        cache.delete(email_ingest_failures_key)
        original_exc_message = exc.args[0]
        raise EmailInboxConnectionError(
            f'Connecting to mailbox {mailbox_identifier} has failed {failures} times out of '
            f'{window_size} connection attempts. The latest failure was: '
            f'{original_exc_message}',
        ) from exc


@shared_task(acks_late=True, priority=9)
def ingest_emails():
    """
    Ingest and process new emails for all mailboxes in the application - i.e.
    those in the MAILBOXES django setting.
    """
    # TODO: remove feature flag check once we are happy with meeting invite
    # email processing
    if not is_feature_flag_active(INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{INTERACTION_EMAIL_INGESTION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        return
    # Acquire a processing lock for the duration of the current DB session -
    # this will ensure that multiple ingestion workers do not run at the same
    # time and therefore prevent the chance of messages being processed more
    # than once
    with advisory_lock('ingest_emails', wait=False) as acquired:
        if not acquired:
            logger.info('Emails are already being ingested by another worker')
            return
        for mailbox in mailbox_handler.get_all_mailboxes():
            try:
                mailbox.process_new_mail()
            except EmailInboxConnectionError as exc:
                handle_connection_error(exc, mailbox.username)
