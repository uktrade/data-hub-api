from logging import getLogger

from celery import shared_task
from dateutil.relativedelta import relativedelta
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
from datahub.investment.project.notification.emails import send_estimated_land_date_reminder
from datahub.investment.project.notification.models import InvestmentNotificationSubscription

logger = getLogger(__name__)

estimated_land_date_notification = InvestmentNotificationSubscription.EstimatedLandDateNotification
TASK_TOKEN_TIMEOUT = 24 * 3600


def get_subscriptions_for_estimated_land_date(notification_type: str):
    """
    Gets subscriptions for estimated land date.

    The notification type is defined as either '30' or '60' days.

    The subscriptions are only returned for advisers who are project managers,
    client relationship managers, project assurance advisers and referral source advisers.
    """
    days = int(notification_type)
    future_estimated_land_date = now() + relativedelta(days=days)

    subscriptions = InvestmentNotificationSubscription.objects.select_related(
        'investment_project',
        'adviser',
    ).filter(
        # the estimated land date subscriptions are only valid for project managers
        # client relationship managers, project assurance advisers and referral source advisers.
        Q(adviser_id=F('investment_project__project_manager_id'))
        | Q(adviser_id=F('investment_project__client_relationship_manager_id'))
        | Q(adviser_id=F('investment_project__project_assurance_adviser_id'))
        | Q(adviser_id=F('investment_project__referral_source_adviser_id')),
        estimated_land_date__contains=[notification_type],
        investment_project__estimated_land_date__year=future_estimated_land_date.year,
        investment_project__estimated_land_date__month=future_estimated_land_date.month,
        investment_project__estimated_land_date__day=future_estimated_land_date.day,
        investment_project__status__in=[
            InvestmentProject.Status.ONGOING,
            InvestmentProject.Status.DELAYED,
        ],
        investment_project__stage_id=InvestmentProjectStage.active.value.id,
    )
    return subscriptions


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def send_estimated_land_date_task():
    """
    The task runs every day for each notification type. It collects the active subscriptions
    and sends a notification if investment project's estimated land date is in 30 or 60 days
    and project manager has active subscription for given days.

    For each notification a token is set with 24h expiration time, in an event when the task
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

        notification_types = estimated_land_date_notification.values

        for notification_type in notification_types:
            subscriptions = get_subscriptions_for_estimated_land_date(notification_type)

            for subscription in subscriptions.iterator():
                token = _get_token_name(
                    subscription.investment_project,
                    subscription.adviser,
                    notification_type,
                )
                if not cache.get(token):
                    cache.set(token, True, TASK_TOKEN_TIMEOUT)
                    send_estimated_land_date_reminder(
                        project=subscription.investment_project,
                        adviser=subscription.adviser,
                        days_left=notification_type,
                    )


def _get_token_name(project, adviser, notification_type):
    token = f'notification:{project.id}-{adviser.id}-{notification_type}'
    return token
