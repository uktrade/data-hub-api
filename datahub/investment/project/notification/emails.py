from functools import lru_cache
from logging import getLogger

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils.timesince import timesince

from datahub.core import statsd
from datahub.investment.project.notification.models import NotificationInnerTemplate
from datahub.notification.constants import NotifyServiceName
from datahub.notification.notify import notify_adviser_by_email

logger = getLogger(__name__)


def send_estimated_land_date_reminder(project, adviser, days_left):
    """
    Sends approaching estimated land date reminder by email.
    """
    statsd.incr(f'send_investment_notification.{days_left}')

    notify_adviser_by_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID,
        get_project_item(project),
        NotifyServiceName.investment,
    )


def send_estimated_land_date_summary(projects, adviser, current_date):
    """
    Sends approaching estimated land date summary reminder by email.
    """
    statsd.incr('send_estimated_land_date_summary')

    notifications = get_projects_summary_list(projects)

    notify_adviser_by_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_SUMMARY_TEMPLATE_ID,
        {
            'month': current_date.strftime('%B'),
            'reminders_number': len(notifications),
            'summary': ''.join(notifications),
            'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
        },
        NotifyServiceName.investment,
    )


def send_no_recent_interaction_reminder(project, adviser, reminder_days, current_date):
    """
    Sends no recent interaction reminder by email.
    """
    statsd.incr(f'send_no_recent_interaction_notification.{reminder_days}')

    item = get_project_item(project)
    last_interaction_date = current_date - relativedelta(days=reminder_days)

    notify_adviser_by_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID,
        {
            **item,
            'time_period': timesince(last_interaction_date, now=current_date).split(',')[0],
            'last_interaction_date': last_interaction_date.strftime('%-d %B %Y'),
        },
        NotifyServiceName.investment,
    )


@lru_cache()
def get_inner_template_content(notification_type):
    inner_template = NotificationInnerTemplate.objects.get(notification_type=notification_type)
    return inner_template.content


def get_project_item(project):
    """Get project item."""
    return {
        'project_details_url': f'{project.get_absolute_url()}/details',
        'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
        'investor_company_name': project.investor_company.name,
        'project_name': project.name,
        'project_code': project.project_code,
        'project_status': project.status.capitalize(),
        'project_stage': project.stage.name,
        # '%-d %B %Y' formats date to 1 January 2022
        'estimated_land_date': project.estimated_land_date.strftime('%-d %B %Y'),
    }


def get_projects_summary_list(projects):
    """Gets formatted projects summary list."""
    notifications = []

    for index, project in enumerate(projects):
        data = {
            'number': index + 1,
            **get_project_item(project),
        }

        notification = get_inner_template_content(
            NotificationInnerTemplate.NotificationType.UPCOMING_ESTIMATED_LAND_DATE,
        )
        for key, value in data.items():
            notification = notification.replace(f'(({key}))', str(value))
        notifications.append(notification)

    return notifications
