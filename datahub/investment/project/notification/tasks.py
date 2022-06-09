import datetime
from logging import getLogger
from operator import attrgetter

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.db.models import F, Q
from django.utils.timezone import now
from django_pglocks import advisory_lock

from datahub.core.constants import InvestmentProjectStage
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.investment.project import (
    INVESTMENT_ESTIMATED_LAND_DATE_NOTIFICATION_FEATURE_FLAG_NAME,
)
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.notification.emails import (
    send_estimated_land_date_reminder,
    send_estimated_land_date_summary,
)
from datahub.investment.project.notification.models import InvestmentNotificationSubscription

logger = getLogger(__name__)

estimated_land_date_notification = InvestmentNotificationSubscription.EstimatedLandDateNotification
TASK_TOKEN_TIMEOUT = 72 * 3600

NOTIFICATION_SUMMARY_THRESHOLD = settings.NOTIFICATION_SUMMARY_THRESHOLD


def get_subscriptions_for_estimated_land_date(adviser_id, current_date: datetime.date):
    """
    Gets subscriptions for estimated land date.

    The notification type is defined as either '30' or '60' days.

    The subscriptions are only returned for advisers who are project managers,
    client relationship managers, project assurance advisers and referral source advisers.
    """
    notification_types = {
        30: current_date + relativedelta(months=1),
        60: current_date + relativedelta(months=2),
    }

    eld_filter = Q()
    for key, value in notification_types.items():
        eld_filter |= Q(
            estimated_land_date__contains=[key],
        ) & Q(investment_project__estimated_land_date=value)

    return InvestmentNotificationSubscription.objects.select_related(
        'investment_project',
        'adviser',
    ).filter(
        eld_filter,
        # the estimated land date subscriptions are only valid for project managers
        # client relationship managers, project assurance advisers and referral source advisers.
        Q(adviser_id=F('investment_project__project_manager_id'))
        | Q(adviser_id=F('investment_project__client_relationship_manager_id'))
        | Q(adviser_id=F('investment_project__project_assurance_adviser_id'))
        | Q(adviser_id=F('investment_project__referral_source_adviser_id')),
        adviser_id=adviser_id,
        investment_project__status__in=[
            InvestmentProject.Status.ONGOING,
            InvestmentProject.Status.DELAYED,
        ],
        investment_project__stage_id=InvestmentProjectStage.active.value.id,
    ).order_by('pk')


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def send_estimated_land_date_task(token_prefix=None):
    """
    The task runs first day of the month for all notification types. It collects the active
    subscriptions and sends a notification if investment project's estimated land date is in
    one or two months (labelled as 30 and 60 days) and project manager has active subscription
    for given days option.

    For each notification a token is set with 72h expiration time, in an event when the task
    gets restarted so that the notifications won't be sent multiple times.
    """
    if not is_feature_flag_active(INVESTMENT_ESTIMATED_LAND_DATE_NOTIFICATION_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag "{INVESTMENT_ESTIMATED_LAND_DATE_NOTIFICATION_FEATURE_FLAG_NAME}"'
            'is not active, '
            'exiting.',
        )
        return

    with advisory_lock('send_estimated_land_date_notifications', wait=False) as acquired:
        if not acquired:
            logger.info(
                'Notifications for estimated land dates are already being processed by '
                'another worker.',
            )
            return

        current_date = now().date().replace(day=1)

        subscriptions_by_adviser = InvestmentNotificationSubscription.objects.distinct(
            'adviser',
        ).iterator()
        for subscription in subscriptions_by_adviser:
            _send_notifications_for_adviser(
                subscription.adviser,
                current_date,
            )


def _send_notifications_for_adviser(
    adviser,
    current_date,
):
    token = _get_token_name(adviser)
    if cache.get(token):
        return

    cache.set(token, True, TASK_TOKEN_TIMEOUT)

    subscriptions = get_subscriptions_for_estimated_land_date(adviser.id, current_date)
    if subscriptions.count() > NOTIFICATION_SUMMARY_THRESHOLD:
        projects = [subscription.investment_project for subscription in subscriptions]
        projects.sort(key=attrgetter('pk'))

        send_estimated_land_date_summary(
            projects=projects,
            adviser=adviser,
            current_date=current_date,
        )
        return

    for subscription in subscriptions.iterator():
        day_diff = (subscription.investment_project.estimated_land_date - current_date).days
        days_left = 30 if day_diff < 32 else 60

        send_estimated_land_date_reminder(
            project=subscription.investment_project,
            adviser=subscription.adviser,
            days_left=days_left,
        )


def _get_token_name(adviser):
    token = f'notification:{adviser.id}'
    return token
