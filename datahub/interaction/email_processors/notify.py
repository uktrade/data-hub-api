from enum import Enum

from celery.utils.log import get_task_logger
from django.conf import settings

from datahub.core import statsd
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.interaction import INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME
from datahub.notification.notify import notify_adviser_by_email


logger = get_task_logger(__name__)


class Template(Enum):
    """
    GOV.UK notifications template ids.
    """

    meeting_ingest_failure = 'fc2c07d5-9f3b-4647-853e-68c324565577'
    meeting_ingest_success = '47418011-3f53-4b39-860a-30969b29781b'


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
    statsd.incr(f'celery.calendar-invite-ingest.failure.{domain_label}')
    if not is_feature_flag_active(INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        return

    flat_recipients = ', '.join(recipients)
    notify_adviser_by_email(
        adviser,
        Template.meeting_ingest_failure.value,
        context={
            'errors': errors,
            'recipients': flat_recipients,
            'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
        },
    )


def notify_meeting_ingest_success(adviser, interaction, recipients):
    """
    Notify an adviser that a meeting ingest has succeeeded - including a link
    to the interaction and intended recipients.
    """
    domain_label = get_domain_label(adviser.get_email_domain())
    statsd.incr(f'celery.calendar-invite-ingest.success.{domain_label}')
    if not is_feature_flag_active(INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{INTERACTION_EMAIL_NOTIFICATION_FEATURE_FLAG_NAME}" is not active, '
            'exiting.',
        )
        return

    flat_recipients = ', '.join(recipients)
    notify_adviser_by_email(
        adviser,
        Template.meeting_ingest_success.value,
        context={
            'interaction_url': interaction.get_absolute_url(),
            'recipients': flat_recipients,
            'support_team_email': settings.DATAHUB_SUPPORT_EMAIL_ADDRESS,
        },
    )
