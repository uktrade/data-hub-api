import logging

from django.conf import settings

from datahub.core import statsd
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.interaction import MAILBOX_NOTIFICATION_FEATURE_FLAG_NAME
from datahub.notification.constants import NotifyServiceName
from datahub.notification.notify import notify_adviser_by_email


logger = logging.getLogger(__name__)


def get_domain_label(domain):
    """
    "." is not a valid character in a prometheus label and the recommended
    practice is to replace it with an "_".
    """
    return domain.replace('.', '_')


def notify_meeting_ingest_failure(adviser, errors, recipients):
    """
    Notify an adviser that a meeting ingest has failed - including error
    details and intended recipients.
    """
    domain_label = get_domain_label(adviser.get_email_domain())
    statsd.incr(f'rq.calendar-invite-ingest.failure.{domain_label}')
    if not is_feature_flag_active(MAILBOX_NOTIFICATION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{MAILBOX_NOTIFICATION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        return

    flat_recipients = ', '.join(recipients)
    notify_adviser_by_email(
        adviser,
        settings.MAILBOX_INGESTION_FAILURE_TEMPLATE_ID,
        context={
            'errors': errors,
            'recipients': flat_recipients,
            'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
        },
        notify_service_name=NotifyServiceName.interaction,
    )


def notify_meeting_ingest_success(adviser, interaction, recipients):
    """
    Notify an adviser that a meeting ingest has succeeeded - including a link
    to the interaction and intended recipients.
    """
    domain_label = get_domain_label(adviser.get_email_domain())
    statsd.incr(f'rq.calendar-invite-ingest.success.{domain_label}')
    if not is_feature_flag_active(MAILBOX_NOTIFICATION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{MAILBOX_NOTIFICATION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        return

    flat_recipients = ', '.join(recipients)
    notify_adviser_by_email(
        adviser,
        settings.MAILBOX_INGESTION_SUCCESS_TEMPLATE_ID,
        context={
            'interaction_url': interaction.get_absolute_url(),
            'recipients': flat_recipients,
            'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
        },
        notify_service_name=NotifyServiceName.interaction,
    )
