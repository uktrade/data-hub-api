from enum import Enum

from datahub.notification.notify import notify_adviser_by_email


class Templates(Enum):
    """
    GOV.UK notifications template ids.
    """

    meeting_ingest_failure = 'fc2c07d5-9f3b-4647-853e-68c324565577'
    meeting_ingest_success = '47418011-3f53-4b39-860a-30969b29781b'


def notify_meeting_ingest_failure(adviser, errors, recipients):
    """
    Notify an adviser that a meeting ingest has failed - including error
    details.
    """
    flat_recipients = ', '.join(recipients)
    notify_adviser_by_email(
        adviser,
        Templates.meeting_ingest_failure.value,
        context={
            'errors': errors,
            'recipients': flat_recipients,
        },
    )


def notify_meeting_ingest_success(adviser, interaction):
    """
    Notify an adviser that a meeting ingest has succeeeded - including a link
    to the interaction.
    """
    notify_adviser_by_email(
        adviser,
        Templates.meeting_ingest_success.value,
        context={
            'interaction_url': interaction.get_absolute_url(),
        },
    )
