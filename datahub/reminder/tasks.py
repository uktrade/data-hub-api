from logging import getLogger

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now
from django_pglocks import advisory_lock

from datahub.core.constants import InvestmentProjectStage
from datahub.investment.project.models import InvestmentProject
from datahub.investment.project.notification.emails import (
    send_estimated_land_date_reminder,
    send_estimated_land_date_summary,
)
from datahub.reminder import ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME
from datahub.reminder.models import (
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)
from datahub.reminder.utils import reminder_days_to_date_filter

NOTIFICATION_SUMMARY_THRESHOLD = settings.NOTIFICATION_SUMMARY_THRESHOLD

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

    fd = now().date().replace(day=1)  # first day of the month
    eld_filter = reminder_days_to_date_filter(fd, subscription.reminder_days)

    projects = InvestmentProject.objects.filter(
        Q(project_manager=subscription.adviser)
        | Q(project_assurance_adviser=subscription.adviser)
        | Q(client_relationship_manager=subscription.adviser)
        | Q(referral_source_adviser=subscription.adviser),
        estimated_land_date__in=eld_filter,
        status__in=[
            InvestmentProject.Status.ONGOING,
            InvestmentProject.Status.DELAYED,
        ],
        stage_id=InvestmentProjectStage.active.value.id,
    ).order_by('pk')

    summary_threshold = projects.count() > NOTIFICATION_SUMMARY_THRESHOLD
    if summary_threshold and subscription.email_reminders_enabled:
        send_estimated_land_date_summary(
            projects=list(projects),
            adviser=subscription.adviser,
            current_date=current_date,
        )

    for project in projects:
        day_diff = (project.estimated_land_date - current_date).days
        days_left = 30 if day_diff < 32 else 60
        create_reminder(
            project=project,
            adviser=subscription.adviser,
            days_left=days_left,
            # don't sent emails for each project is summary notification threshold has been reached
            send_email=(subscription.email_reminders_enabled and not summary_threshold),
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
