from notifications_python_client.notifications import NotificationsAPIClient
from unittest import mock
import warnings

from django.conf import settings
from datahub.notification.constants import NotifyServiceName
from datahub.notification.notify import notify_by_email


from datahub.task.constants import Template


def _send_email(**data):
    """Send email in a separate thread."""
    notify_by_email(
        data['email_address'],
        data['template_id'],
        data.get('personalisation'),
        NotifyServiceName.datahub,
    )


def _prepare_personalisation(task, data=None):
    """Prepare the personalisation data with common values."""
    return {
        'task title': task.title,
        'modified by': task.modified_by,
        'company name': 'A Company',
        'task due date': task.due_date,
        'embedded link': 'task.get_datahub_frontend_url()',
        **(data or {}),
    }


def notify_adviser_added_to_task(task, adviser):
    """
    Send a notification to the customer and the advisers
    that a quote has just been cancelled.
    """
    #  notify customer
    _send_email(
        email_address=adviser.get_current_email(),
        template_id=Template.task_assigned_to_others.value,
        personalisation=_prepare_personalisation(
            task,
            {
                'recipient name': adviser.name,
            },
        ),
    )
