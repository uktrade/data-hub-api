import warnings
from unittest import mock

from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient


class NotificationClient:
    """
    """

    def __init__(self):
        """Init underlying notification client."""
        if settings.DATAHUB_NOTIFICATION_API_KEY:
            self.client = NotificationsAPIClient(
                settings.DATAHUB_NOTIFICATION_API_KEY,
            )
        else:
            self.client = mock.Mock(spec_set=NotificationsAPIClient)
            warnings.warn(
                '`settings.DATAHUB_NOTIFICATION_API_KEY` not specified therefore all '
                'Data Hub notifications will be mocked. '
                "You might want to change this if it's not a "
                'testing or development environment.',
                RuntimeWarning,
                stacklevel=2,
            )

    def send_email_notification(
        self,
        recipient_email,
        template_identifier,
        context=None,
    ):
        if not context:
            context = {}
        self.client.send_email_notification(
            email_address=recipient_email,
            template_id=template_identifier,
            personalisation=context,
        )


client = NotificationClient()
