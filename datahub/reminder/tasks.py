from logging import getLogger

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q
from django.utils.timesince import timesince
from django.utils.timezone import now
from django_pglocks import advisory_lock

from datahub.core import statsd
from datahub.core.constants import InvestmentProjectStage
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.notification.constants import NotifyServiceName
from datahub.notification.tasks import send_email_notification
from datahub.reminder import (
    ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
    NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
)
from datahub.reminder.emails import (
    get_project_item,
    get_projects_summary_list,
)
from datahub.reminder.models import (
    NoRecentInvestmentInteractionReminder,
    NoRecentInvestmentInteractionSubscription,
    UpcomingEstimatedLandDateReminder,
    UpcomingEstimatedLandDateSubscription,
)
from datahub.reminder.utils import (
    reminder_days_to_estimated_land_date_filter,
)

NOTIFICATION_SUMMARY_THRESHOLD = settings.NOTIFICATION_SUMMARY_THRESHOLD

logger = getLogger(__name__)


def send_estimated_land_date_reminder(project, adviser, days_left, reminders):
    """
    Sends approaching estimated land date reminder by email.
    """
    statsd.incr(f'send_investment_notification.{days_left}')

    notify_adviser_by_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID,
        get_project_item(project),
        reminders,
    )


def send_estimated_land_date_summary(projects, adviser, current_date, reminders):
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
        reminders,
    )


def send_no_recent_interaction_reminder(project, adviser, reminder_days, current_date, reminders):
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
        reminders,
    )


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def update_estimated_land_date_reminder_email_status(email_notification_id, reminder_ids):
    reminders = UpcomingEstimatedLandDateReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def update_no_recent_interaction_reminder_email_status(email_notification_id, reminder_ids):
    reminders = NoRecentInvestmentInteractionReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


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
        for subscription in UpcomingEstimatedLandDateSubscription.objects.select_related(
            'adviser',
        ).filter(adviser__is_active=True).iterator():
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

    first_day_of_the_month = now().date().replace(day=1)
    eld_filter = reminder_days_to_estimated_land_date_filter(
        first_day_of_the_month,
        subscription.reminder_days,
    )

    projects = _get_active_projects(
        subscription.adviser,
    ).filter(
        estimated_land_date__in=eld_filter,
    ).order_by('pk')

    if _has_existing_estimated_land_date_reminder(
        projects[0],
        subscription.adviser,
        current_date,
    ):
        return

    summary_threshold = projects.count() > NOTIFICATION_SUMMARY_THRESHOLD

    reminders = [
        create_estimated_land_date_reminder(
            project=project,
            adviser=subscription.adviser,
            # don't send emails for each project if summary notification threshold has been
            # reached
            send_email=(subscription.email_reminders_enabled and not summary_threshold),
            current_date=current_date,
        ) for project in projects
    ]

    if summary_threshold and subscription.email_reminders_enabled:
        send_estimated_land_date_summary(
            projects=list(projects),
            adviser=subscription.adviser,
            current_date=current_date,
            reminders=reminders,
        )


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def generate_no_recent_interaction_reminders():
    """
    Generates No Recent Interaction Reminders according to each adviser's Subscriptions
    """
    with advisory_lock('generate_no_recent_interaction_reminders', wait=False) as acquired:
        if not acquired:
            logger.info(
                'Reminders for no recent interactions are already being '
                'processed by another worker.',
            )
            return
        current_date = now().date()
        for subscription in NoRecentInvestmentInteractionSubscription.objects.select_related(
            'adviser',
        ).filter(adviser__is_active=True).iterator():
            generate_no_recent_interaction_reminders_for_subscription(
                subscription=subscription,
                current_date=current_date,
            )


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
def generate_no_recent_interaction_reminders_for_subscription(subscription, current_date):
    """
    Generates the no recent interaction reminders for a given subscription.
    """
    user_features = subscription.adviser.features.filter(
        is_active=True,
    ).values_list('code', flat=True)
    if NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME not in user_features:
        logger.info(
            f'Feature flag "{NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME}"'
            'is not active for this user, exiting.',
        )
        return

    for reminder_day in subscription.reminder_days:
        threshold = current_date - relativedelta(days=reminder_day)

        for project in _get_active_projects(subscription.adviser).iterator():
            qs = Interaction.objects.filter(investment_project_id=project.id)
            has_interactions = qs.exists()
            if has_interactions:
                exists = qs.filter(created_on__date=threshold).exists()
                if not exists:
                    continue
                send_reminder = not qs.filter(created_on__date__gt=threshold).exists()
            else:
                send_reminder = project.created_on.date() == threshold

            if send_reminder:
                create_no_recent_interaction_reminder(
                    project=project,
                    adviser=subscription.adviser,
                    reminder_days=reminder_day,
                    send_email=subscription.email_reminders_enabled,
                    current_date=current_date,
                )


def create_estimated_land_date_reminder(project, adviser, send_email, current_date):
    """
    Creates a reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    if _has_existing_estimated_land_date_reminder(project, adviser, current_date):
        return

    day_diff = (project.estimated_land_date - current_date).days
    days_left = 30 if day_diff < 32 else 60

    reminder = UpcomingEstimatedLandDateReminder.objects.create(
        adviser=adviser,
        event=f'{days_left} days left to estimated land date',
        project=project,
    )

    if send_email:
        send_estimated_land_date_reminder(
            project=project,
            adviser=adviser,
            days_left=days_left,
            reminders=[reminder],
        )

    return reminder


def _has_existing_estimated_land_date_reminder(project, adviser, current_date):
    return UpcomingEstimatedLandDateReminder.objects.filter(
        adviser=adviser,
        project=project,
        created_on__month=current_date.month,
        created_on__year=current_date.year,
    ).exists()


def create_no_recent_interaction_reminder(
    project,
    adviser,
    reminder_days,
    send_email,
    current_date,
):
    """
    Creates a no recent interaction reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    last_interaction_date = current_date - relativedelta(days=reminder_days)
    days_text = timesince(last_interaction_date, now=current_date).split(',')[0]
    has_existing = NoRecentInvestmentInteractionReminder.objects.filter(
        adviser=adviser,
        event=f'No recent interaction with {project.name} in {days_text}',
        project=project,
        created_on__date=current_date,
    ).exists()

    if has_existing:
        return

    reminder = NoRecentInvestmentInteractionReminder.objects.create(
        adviser=adviser,
        event=f'No recent interaction with {project.name} in {days_text}',
        project=project,
    )

    if send_email:
        send_no_recent_interaction_reminder(
            project=project,
            adviser=adviser,
            reminder_days=reminder_days,
            current_date=current_date,
            reminders=[reminder],
        )


def notify_adviser_by_email(adviser, template_identifier, context, reminders=None):
    """
    Notify an adviser, using a GOVUK notify template and some template context.

    Link a separate task to store notification_id, so it is possible to track the
    status of email delivery.
    """
    status_update_task = {
        'UpcomingEstimatedLandDateReminder': update_estimated_land_date_reminder_email_status,
        'NoRecentInvestmentInteractionReminder':
            update_no_recent_interaction_reminder_email_status,
    }
    link_task = {}
    if reminders and len(reminders) > 0:
        class_name = reminders[0].__class__.__name__
        link_task['link'] = status_update_task[class_name].s(
            [reminder.id for reminder in reminders],
        )

    email_address = adviser.get_current_email()
    send_email_notification.apply_async(
        args=(email_address, template_identifier),
        kwargs={
            'context': context,
            'notify_service_name': NotifyServiceName.investment,
        },
        **link_task,
    )


def _get_active_projects(adviser):
    """Get active projects for given adviser."""
    return InvestmentProject.objects.filter(
        Q(project_manager=adviser)
        | Q(project_assurance_adviser=adviser)
        | Q(client_relationship_manager=adviser)
        | Q(referral_source_adviser=adviser),
        status__in=[
            InvestmentProject.Status.ONGOING,
            InvestmentProject.Status.DELAYED,
        ],
        stage_id=InvestmentProjectStage.active.value.id,
    )
