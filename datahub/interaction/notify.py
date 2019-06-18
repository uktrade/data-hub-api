from enum import Enum

from datahub.notification.notify import notify_adviser


class Templates(Enum):
    """GOV.UK notifications template ids."""

    meeting_invite_ingest_failure = 'fc2c07d5-9f3b-4647-853e-68c324565577'


def notify_meeting_ingest_failure(adviser, errors, recipients):
    flat_errors = [
        'Subject: This should be less than 80 characters',
        'Contacts: There were no recipients known by as contacts in Data Hub',
    ]
    flat_recipients = ', '.join(recipients)
    notify_adviser(
        adviser,
        Templates.meeting_invite_ingest_failure.value,
        context={
            'errors': flat_errors,
            'recipients': flat_recipients,
        },
    )
