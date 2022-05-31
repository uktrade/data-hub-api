from logging import getLogger

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils.timezone import now
from django_pglocks import advisory_lock

from datahub.core.constants import InvestmentProjectStage
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.notification.emails import send_estimated_land_date_reminder
from datahub.reminder import ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME
from datahub.reminder.models import (
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)


logger = getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def generate_estimated_land_date_reminders():
    """
    Generates Estimated Land Date Reminders according to each adviser's Subscriptions
    """
    with advisory_lock('generate_estimated_land_date_reminders', wait=False) as acquired:
        if not acquired:
            logger.info(
                'Reminders for approaching estimated land dates are already being '
                'processed by another worker.',
            )
            return
        current_date = now().date()
        for subscription in UpcomingEstimatedLandDateSubscription.objects.all().iterator():
            generate_estimated_land_date_reminders_for_subscription(
                subscription=subscription,
                current_date=current_date,
            )


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def generate_estimated_land_date_reminders_for_subscription(subscription, current_date):
    """
    Generates the estimated land date reminders for a given subscription.
    """
    user_features = subscription.adviser.features.filter(
        is_active=True,
    ).values_list('code', flat=True)
    if ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME not in user_features:
        logger.info(
            f'Feature flag "{ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME}"'
            'is not active for this user, exiting.',
        )
        return
    for days_left in subscription.reminder_days:
        for project in InvestmentProject.objects.filter(
            Q(project_manager=subscription.adviser)
            | Q(project_assurance_adviser=subscription.adviser)
            | Q(client_relationship_manager=subscription.adviser)
            | Q(referral_source_adviser=subscription.adviser),
            estimated_land_date=current_date + relativedelta(days=days_left),
        ).exclude(
            stage__in=[
                InvestmentProjectStage.verify_win.value.id,
                InvestmentProjectStage.won.value.id,
            ],
        ):
            create_reminder(
                project=project,
                adviser=subscription.adviser,
                days_left=days_left,
                send_email=subscription.email_reminders_enabled,
                current_date=current_date,
            )


def create_reminder(project, adviser, days_left, send_email, current_date):
    """
    Creates a reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    has_existing = UpcomingEstimatedLandDateReminder.objects.filter(
        adviser=adviser,
        event=f'{days_left} days left to estimated land date',
        project=project,
        created_on__date=current_date,
    ).exists()

    if has_existing:
        return

    UpcomingEstimatedLandDateReminder.objects.create(
        adviser=adviser,
        event=f'{days_left} days left to estimated land date',
        project=project,
    )

    if send_email:
        send_estimated_land_date_reminder(
            project=project,
            adviser=adviser,
            days_left=days_left,
        )
