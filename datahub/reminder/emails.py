from functools import lru_cache
from logging import getLogger

from django.conf import settings

from datahub.investment.project.notification.models import NotificationInnerTemplate

logger = getLogger(__name__)


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
