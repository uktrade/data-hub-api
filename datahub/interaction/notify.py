from enum import Enum

from datahub.notification.notify import notify_adviser


class Templates(Enum):
    """
    GOV.UK notifications template ids.
    """

    meeting_ingest_failure = 'fc2c07d5-9f3b-4647-853e-68c324565577'


def notify_meeting_ingest_failure(adviser, errors, recipients):
    flat_recipients = ', '.join(recipients)
    notify_adviser(
        adviser,
        Templates.meeting_ingest_failure.value,
        context={
            'errors': errors,
            'recipients': flat_recipients,
        },
    )
