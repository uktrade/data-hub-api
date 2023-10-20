from notifications_python_client.notifications import NotificationsAPIClient
from unittest import mock
import warnings

from django.conf import settings
from datahub.notification.constants import NotifyServiceName
from datahub.notification.notify import notify_by_email


from datahub.task.constants import Template


class Notify:
    """
    Used to send notifications when an adviser has been added to a task.
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
                'Task notifications will be mocked. '
                "You might want to change this if it's not a "
                'testing or development environment.',
                RuntimeWarning,
                stacklevel=2,
            )

    def _send_email(self, **data):
        """Send email in a separate thread."""
        notify_by_email(
            data['email_address'],
            data['template_id'],
            data.get('personalisation'),
            NotifyServiceName.datahub,
        )

    def _prepare_personalisation(self, task, data=None):
        """Prepare the personalisation data with common values."""
        return {
            'task title': task.title,
            'modified by': task.modified_by,
            'company name': task.company.name,
            'task due date': task.due_date,
            'embedded link': task.get_datahub_frontend_url(),
            **(data or {}),
        }

    def notify_adviser_added_to_task(self, task, adviser):
        """
        Send a notification to the customer and the advisers
        that a quote has just been cancelled.
        """
        #  notify customer
        self._send_email(
            email_address=adviser.get_current_email(),
            template_id=Template.task_assigned_to_others.value,
            personalisation=self._prepare_personalisation(
                task,
                {
                    'recipient name': task.adviser.name,
                },
            ),
        )


notify = Notify()
