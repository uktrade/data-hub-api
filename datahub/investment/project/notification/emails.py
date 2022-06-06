from logging import getLogger

from django.conf import settings

from datahub.core import statsd
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
        {
            'project_details_url': f'{project.get_absolute_url()}/details',
            'project_subscription_url': f'{project.get_absolute_url()}/notifications/'
                                        'estimated-land-date',
            'investor_company_name': project.investor_company.name,
            'project_name': project.name,
            'project_code': project.project_code,
            'project_status': project.status.capitalize(),
            'project_stage': project.stage.name,
            # '%-d %B %Y' formats date to 1 January 2022
            'estimated_land_date': project.estimated_land_date.strftime('%-d %B %Y'),
        },
        NotifyServiceName.investment,
    )
