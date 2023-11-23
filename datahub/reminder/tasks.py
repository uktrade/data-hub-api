from logging import getLogger


from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q
from django.utils.timesince import timesince
from django.utils.timezone import now
from django_pglocks import advisory_lock

from datahub.company.constants import (
    OneListTierID,
)
from datahub.company.models import (
    Company,
    OneListCoreTeamMember,
)
from datahub.core import statsd
from datahub.core.constants import (
    InvestmentProjectStage,
)
from datahub.core.queues.constants import (
    HALF_DAY_IN_SECONDS,
)
from datahub.core.queues.job_scheduler import (
    job_scheduler,
)
from datahub.core.queues.scheduler import (
    LONG_RUNNING_QUEUE,
)
from datahub.feature_flag.utils import (
    is_feature_flag_active,
    is_user_feature_flag_active,
)
from datahub.interaction.models import Interaction
from datahub.investment.project.models import (
    InvestmentProject,
)
from datahub.notification.constants import (
    NotifyServiceName,
)
from datahub.notification.core import (
    notify_gateway,
)
from datahub.reminder import (
    EXPORT_NEW_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    EXPORT_NEW_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
    EXPORT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    EXPORT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
    INVESTMENT_ESTIMATED_LAND_DATE_EMAIL_STATUS_FEATURE_FLAG_NAME,
    INVESTMENT_ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
    INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
)
from datahub.reminder.emails import (
    get_company_item,
    get_interaction_item,
    get_project_item,
    get_projects_summary_list,
)
from datahub.reminder.models import (
    EmailDeliveryStatus,
    NewExportInteractionReminder,
    NewExportInteractionSubscription,
    NoRecentExportInteractionReminder,
    NoRecentExportInteractionSubscription,
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

    notify_adviser_by_rq_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_TEMPLATE_ID,
        get_project_item(project),
        update_estimated_land_date_reminder_email_status,
        reminders,
    )


def send_estimated_land_date_summary(projects, adviser, current_date, reminders):
    """
    Sends approaching estimated land date summary reminder by email.
    """
    statsd.incr('send_estimated_land_date_summary')

    notifications = get_projects_summary_list(projects)

    notify_adviser_by_rq_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_ESTIMATED_LAND_DATE_SUMMARY_TEMPLATE_ID,
        {
            'month': current_date.strftime('%B'),
            'reminders_number': len(notifications),
            'summary': ''.join(notifications),
            'settings_url': settings.DATAHUB_FRONTEND_REMINDER_SETTINGS_URL,
        },
        update_estimated_land_date_reminder_email_status,
        reminders,
    )


def send_no_recent_export_interaction_reminder(
    company,
    interaction,
    adviser,
    reminder_days,
    current_date,
    reminders,
):
    """
    Sends no recent export interaction reminder by email.
    """
    statsd.incr(f'send_no_recent_export_interaction_notification.{reminder_days}')

    item = get_company_item(company)
    last_interaction_date = current_date - relativedelta(days=reminder_days)

    params = {
        **item,
        'time_period': timesince(last_interaction_date, now=current_date).split(',')[0],
        'last_interaction_date': last_interaction_date.strftime('%-d %B %Y'),
    }

    if interaction:
        template_id = settings.EXPORT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID
        interaction_item = get_interaction_item(interaction)
        params.update(interaction_item)
    else:
        template_id = settings.EXPORT_NOTIFICATION_NO_INTERACTION_TEMPLATE_ID

    notify_adviser_by_rq_email(
        adviser,
        template_id,
        params,
        update_no_recent_export_interaction_reminder_email_status,
        reminders,
    )


def send_new_export_interaction_reminder(
    company,
    interaction,
    adviser,
    reminder_days,
    current_date,
    reminders,
):
    """Sends new export interaction reminder by email."""
    statsd.incr(f'send_new_export_interaction_notification.{reminder_days}')

    item = get_company_item(company)
    last_interaction_date = current_date - relativedelta(days=reminder_days)

    params = {
        **item,
        'last_interaction_date': last_interaction_date.strftime('%-d %B %Y'),
    }

    template_id = settings.EXPORT_NOTIFICATION_NEW_INTERACTION_TEMPLATE_ID
    interaction_item = get_interaction_item(interaction)
    params.update(interaction_item)

    notify_adviser_by_rq_email(
        adviser,
        template_id,
        params,
        update_new_export_interaction_reminder_email_status,
        reminders,
    )


def send_no_recent_interaction_reminder(
    project,
    adviser,
    reminder_days,
    current_date,
    reminders,
):
    """
    Sends no recent interaction reminder by email.
    """
    statsd.incr(f'send_no_recent_interaction_notification.{reminder_days}')

    item = get_project_item(project)
    last_interaction_date = current_date - relativedelta(days=reminder_days)

    notify_adviser_by_rq_email(
        adviser,
        settings.INVESTMENT_NOTIFICATION_NO_RECENT_INTERACTION_TEMPLATE_ID,
        {
            **item,
            'time_period': timesince(last_interaction_date, now=current_date).split(',')[0],
            'last_interaction_date': last_interaction_date.strftime('%-d %B %Y'),
        },
        update_no_recent_interaction_reminder_email_status,
        reminders,
    )


def update_estimated_land_date_reminder_email_status(email_notification_id, reminder_ids):
    reminders = UpcomingEstimatedLandDateReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_estimated_land_date_reminder_email_status completed'
        f'email_notification_id to {email_notification_id} and reminder_ids set to {reminder_ids}',
    )


def update_no_recent_interaction_reminder_email_status(email_notification_id, reminder_ids):
    reminders = NoRecentInvestmentInteractionReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_no_recent_interaction_reminder_email_status completed'
        f'email_notification_id to {email_notification_id} and reminder_ids set to {reminder_ids}',
    )


def update_no_recent_export_interaction_reminder_email_status(email_notification_id, reminder_ids):
    reminders = NoRecentExportInteractionReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()

    logger.info(
        'Task update_no_recent_export_interaction_reminder_email_status completed'
        f'email_notification_id to {email_notification_id} and reminder_ids set to {reminder_ids}',
    )


def schedule_generate_estimated_land_date_reminders():
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=generate_estimated_land_date_reminders,
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )
    logger.info(
        f'Task {job.id} generate_estimated_land_date_reminders scheduled',
    )
    return job


def update_new_export_interaction_reminder_email_status(email_notification_id, reminder_ids):
    reminders = NewExportInteractionReminder.all_objects.filter(id__in=reminder_ids)
    for reminder in reminders:
        reminder.email_notification_id = email_notification_id
        reminder.save()


def generate_estimated_land_date_reminders():
    """
    Generates Estimated Land Date Reminders according to each adviser's Subscriptions
    """
    with advisory_lock(
        'generate_estimated_land_date_reminders',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Reminders for approaching estimated land dates are already being '
                'processed by another worker.',
            )
            return
        current_date = now().date()
        for subscription in (
            UpcomingEstimatedLandDateSubscription.objects.select_related(
                'adviser',
            )
            .filter(adviser__is_active=True)
            .iterator()
        ):
            schedule_generate_estimated_land_date_reminders_for_subscription(
                subscription=subscription,
                current_date=current_date,
            )

    logger.info(
        'Task generate_estimated_land_date_reminders completed',
    )


def schedule_generate_estimated_land_date_reminders_for_subscription(subscription, current_date):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=generate_estimated_land_date_reminders_for_subscription,
        function_kwargs={
            'subscription': subscription,
            'current_date': current_date,
        },
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )
    logger.info(
        f'Task {job.id} generate_estimated_land_date_reminders_for_subscription scheduled '
        f'subscription set to {subscription} and current_date set to {current_date}',
    )
    return job


def generate_estimated_land_date_reminders_for_subscription(subscription, current_date):
    """
    Generates the estimated land date reminders for a given subscription.
    """
    if not is_user_feature_flag_active(
        INVESTMENT_ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME,
        subscription.adviser,
    ):
        logger.info(
            f'Feature flag {INVESTMENT_ESTIMATED_LAND_DATE_REMINDERS_FEATURE_FLAG_NAME}'
            f'is not active for this user with ID {subscription.adviser.id}, exiting.',
        )
        return

    first_day_of_the_month = now().date().replace(day=1)
    eld_filter = reminder_days_to_estimated_land_date_filter(
        first_day_of_the_month,
        subscription.reminder_days,
    )

    projects = (
        _get_active_projects(
            subscription.adviser,
        )
        .filter(
            estimated_land_date__in=eld_filter,
        )
        .order_by('pk')
    )

    if not projects.exists() or _has_existing_estimated_land_date_reminder(
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
        )
        for project in projects
    ]

    if summary_threshold and subscription.email_reminders_enabled:
        send_estimated_land_date_summary(
            projects=list(projects),
            adviser=subscription.adviser,
            current_date=current_date,
            reminders=reminders,
        )

    logger.info(
        'Task generate_estimated_land_date_reminders_for_subscription completed',
        f'subscription set to {subscription} and current_date set to {current_date}',
    )


def generate_no_recent_interaction_reminders():
    """
    Generates No Recent Interaction Reminders according to each adviser's Subscriptions
    """
    with advisory_lock(
        'generate_no_recent_interaction_reminders',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Reminders for no recent interactions are already being '
                'processed by another worker.',
            )
            return
        current_date = now().date()
        for subscription in (
            NoRecentInvestmentInteractionSubscription.objects.select_related(
                'adviser',
            )
            .filter(adviser__is_active=True)
            .iterator()
        ):
            job_scheduler(
                function=generate_no_recent_interaction_reminders_for_subscription,
                function_args=(
                    subscription,
                    current_date,
                ),
                max_retries=5,
                queue_name=LONG_RUNNING_QUEUE,
                retry_backoff=True,
                retry_intervals=30,
            )


def generate_no_recent_interaction_reminders_for_subscription(subscription, current_date):
    """
    Generates the no recent interaction reminders for a given subscription.
    """
    if not is_user_feature_flag_active(
        INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        subscription.adviser,
    ):
        logger.info(
            f'Feature flag {INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME}'
            f'is not active for this user with ID {subscription.adviser.id}, exiting.',
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
                send_reminder = project.created_on and project.created_on.date() == threshold

            if send_reminder:
                create_no_recent_interaction_reminder(
                    project=project,
                    adviser=subscription.adviser,
                    reminder_days=reminder_day,
                    send_email=subscription.email_reminders_enabled,
                    current_date=current_date,
                )


def generate_no_recent_export_interaction_reminders():
    """
    Generates No Recent Export Interaction Reminders according to each adviser's Subscriptions
    """
    with advisory_lock(
        'generate_no_recent_export_interaction_reminders',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Reminders for no recent export interactions are already being '
                'processed by another worker.',
            )
            return
        current_date = now().date()
        for subscription in (
            NoRecentExportInteractionSubscription.objects.select_related(
                'adviser',
            )
            .filter(adviser__is_active=True)
            .iterator()
        ):
            job = job_scheduler(
                queue_name=LONG_RUNNING_QUEUE,
                function=generate_no_recent_export_interaction_reminders_for_subscription,
                function_kwargs={
                    'subscription': subscription,
                    'current_date': current_date,
                },
                max_retries=5,
                retry_backoff=True,
                retry_intervals=30,
            )

            logger.info(
                f'Task {job.id} generate_no_recent_export_interaction_reminders_for_subscription',
            )


def generate_no_recent_export_interaction_reminders_for_subscription(subscription, current_date):
    """
    Generates the no recent export interaction reminders for a given subscription.
    """
    if not is_user_feature_flag_active(
        EXPORT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        subscription.adviser,
    ):
        logger.info(
            f'Feature flag {EXPORT_NO_RECENT_INTERACTION_REMINDERS_FEATURE_FLAG_NAME}'
            f'is not active for this user with ID {subscription.adviser.id}, exiting.',
        )
        return

    for reminder_day in subscription.reminder_days:
        threshold = current_date - relativedelta(days=reminder_day)

        for company in _get_managed_companies(subscription.adviser).iterator():
            qs = Interaction.objects.filter(companies__in=[company])
            has_interactions = qs.exists()

            if has_interactions:
                exists = qs.filter(created_on__date=threshold).exists()
                if not exists:
                    continue
                send_reminder = not qs.filter(created_on__date__gt=threshold).exists()
                reminder_interaction = qs.order_by('created_on').last()
            else:
                send_reminder = company.created_on and company.created_on.date() == threshold
                reminder_interaction = None

            if send_reminder:
                create_no_recent_export_interaction_reminder(
                    company=company,
                    adviser=subscription.adviser,
                    interaction=reminder_interaction,
                    reminder_days=reminder_day,
                    send_email=subscription.email_reminders_enabled,
                    current_date=current_date,
                )


def generate_new_export_interaction_reminders():
    """
    Generates New Export Interaction Reminders according to each adviser's Subscriptions
    """
    with advisory_lock(
        'generate_new_export_interaction_reminders',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Reminders for new export interactions are already being '
                'processed by another worker.',
            )
            return
        current_date = now().date()
        for subscription in (
            NewExportInteractionSubscription.objects.select_related(
                'adviser',
            )
            .filter(adviser__is_active=True)
            .iterator()
        ):
            job = job_scheduler(
                queue_name=LONG_RUNNING_QUEUE,
                function=generate_new_export_interaction_reminders_for_subscription,
                function_kwargs={
                    'subscription': subscription,
                    'current_date': current_date,
                },
                max_retries=5,
                retry_backoff=True,
                retry_intervals=30,
            )

            logger.info(
                f'Task {job.id} generate_new_export_interaction_reminders_for_subscription',
            )


def generate_new_export_interaction_reminders_for_subscription(subscription, current_date):
    """
    Generates the new export interaction reminders for a given subscription.
    """
    if not is_user_feature_flag_active(
        EXPORT_NEW_INTERACTION_REMINDERS_FEATURE_FLAG_NAME,
        subscription.adviser,
    ):
        logger.info(
            f'Feature flag {EXPORT_NEW_INTERACTION_REMINDERS_FEATURE_FLAG_NAME}'
            f'is not active for this user with ID {subscription.adviser.id}, exiting.',
        )
        return

    for reminder_day in subscription.reminder_days:
        threshold = current_date - relativedelta(days=reminder_day)

        for company in _get_managed_companies(subscription.adviser).iterator():
            qs = Interaction.objects.filter(
                companies__in=[company],
                created_on__date=threshold,
            ).exclude(
                Q(created_by=subscription.adviser) | Q(modified_by=subscription.adviser),
            )
            has_interactions = qs.exists()

            if has_interactions:
                reminder_interaction = qs.order_by('created_on').last()

                create_new_export_interaction_reminder(
                    company=company,
                    adviser=subscription.adviser,
                    interaction=reminder_interaction,
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


def create_no_recent_export_interaction_reminder(
    company,
    adviser,
    interaction,
    reminder_days,
    send_email,
    current_date,
):
    """
    Creates a no recent export interaction reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    last_interaction_date = current_date - relativedelta(days=reminder_days)
    days_text = timesince(last_interaction_date, now=current_date).split(',')[0]
    has_existing = NoRecentExportInteractionReminder.objects.filter(
        adviser=adviser,
        event=f'No recent interaction with {company.name} in {days_text}',
        company=company,
        created_on__date=current_date,
    ).exists()

    if has_existing:
        return

    reminder = NoRecentExportInteractionReminder.objects.create(
        adviser=adviser,
        event=f'No recent interaction with {company.name} in {days_text}',
        company=company,
        interaction=interaction,
    )

    if send_email:
        send_no_recent_export_interaction_reminder(
            company=company,
            interaction=interaction,
            adviser=adviser,
            reminder_days=reminder_days,
            current_date=current_date,
            reminders=[reminder],
        )


def create_new_export_interaction_reminder(
    company,
    adviser,
    interaction,
    reminder_days,
    send_email,
    current_date,
):
    """
    Creates a new export interaction reminder and sends an email if required.

    If a reminder has already been sent on the same day, then do nothing.
    """
    has_existing = NewExportInteractionReminder.objects.filter(
        adviser=adviser,
        event=f'New interaction with {company.name}',
        company=company,
        created_on__date=current_date,
    ).exists()

    if has_existing:
        return

    reminder = NewExportInteractionReminder.objects.create(
        adviser=adviser,
        event=f'New interaction with {company.name}',
        company=company,
        interaction=interaction,
    )

    if send_email:
        send_new_export_interaction_reminder(
            company=company,
            interaction=interaction,
            adviser=adviser,
            reminder_days=reminder_days,
            current_date=current_date,
            reminders=[reminder],
        )


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


def notify_adviser_by_rq_email(
    adviser,
    template_identifier,
    context,
    update_task,
    reminders=None,
):
    """
    Notify an adviser, using a GOVUK notify template and some template context.

    Link a separate task to store notification_id, so it is possible to track the
    status of email delivery.

    Note: this should replace notify_adviser_by_email as we move towards using RQ.
    """
    email_address = adviser.get_current_email()
    job = job_scheduler(
        function=send_email_notification_via_rq,
        function_args=(
            email_address,
            template_identifier,
            update_task,
            [reminder.id for reminder in reminders] if reminders else None,
            context,
            NotifyServiceName.investment,
        ),
        retry_backoff=True,
        max_retries=5,
    )

    return job


def send_email_notification_via_rq(
    recipient_email,
    template_identifier,
    update_delivery_status_task=None,
    reminder_ids=None,
    context=None,
    notify_service_name=None,
):
    """
    Email notification function to be scheduled by RQ,
    setting up a second task to update the email delivery status.
    """
    logger.info(
        f'send_email_notification_via_rq attempting to send email to recipient {recipient_email},'
        f'using template identifier {template_identifier}',
    )
    response = notify_gateway.send_email_notification(
        recipient_email,
        template_identifier,
        context,
        notify_service_name,
    )

    logger.info(
        f'send_email_notification_via_rq email sent to recipient {recipient_email},'
        f'received response {response}',
    )

    job_scheduler(
        function=update_delivery_status_task,
        function_args=(
            response['id'],
            reminder_ids,
        ),
        queue_name=LONG_RUNNING_QUEUE,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )

    logger.info(
        'Task send_email_notification_via_rq completed'
        f'email_notification_id to {response["id"]} and reminder_ids set to {reminder_ids}',
    )

    return response['id'], reminder_ids


def update_notify_email_delivery_status_for_estimated_land_date():
    if not is_feature_flag_active(INVESTMENT_ESTIMATED_LAND_DATE_EMAIL_STATUS_FEATURE_FLAG_NAME):
        logger.info(
            f'Feature flag {INVESTMENT_ESTIMATED_LAND_DATE_EMAIL_STATUS_FEATURE_FLAG_NAME}'
            ' is not active, exiting.',
        )
        return

    with advisory_lock(
        'update_estimated_land_date_email_delivery',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Email status checks for approaching estimated land dates are already being '
                'processed by another worker.',
            )
            return
        current_date = now()
        date_threshold = current_date - relativedelta(days=4)

        notification_ids = (
            UpcomingEstimatedLandDateReminder.all_objects.filter(
                Q(email_delivery_status=EmailDeliveryStatus.UNKNOWN)
                | Q(email_delivery_status=EmailDeliveryStatus.SENDING),
                created_on__gte=date_threshold,
                email_notification_id__isnull=False,
            )
            .values_list('email_notification_id', flat=True)
            .distinct()
        )
        for notification_id in notification_ids:
            result = notify_gateway.get_notification_by_id(
                notification_id,
                notify_service_name=NotifyServiceName.investment,
            )
            if 'status' in result:
                UpcomingEstimatedLandDateReminder.all_objects.filter(
                    email_notification_id=notification_id,
                ).update(
                    email_delivery_status=result['status'],
                    modified_on=now(),
                )


def update_notify_email_delivery_status_for_no_recent_export_interaction():
    if not is_feature_flag_active(
        EXPORT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    ):
        logger.info(
            f'Feature flag {EXPORT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME}'
            ' is not active, exiting.',
        )
        return

    with advisory_lock(
        'update_no_recent_export_interaction_email_delivery',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Email status checks for no recent export interaction are already '
                'being processed by another worker.',
            )
            return
        current_date = now()
        date_threshold = current_date - relativedelta(days=4)

        notification_ids = (
            NoRecentExportInteractionReminder.all_objects.filter(
                Q(email_delivery_status=EmailDeliveryStatus.UNKNOWN)
                | Q(email_delivery_status=EmailDeliveryStatus.SENDING),
                created_on__gte=date_threshold,
                email_notification_id__isnull=False,
            )
            .values_list('email_notification_id', flat=True)
            .distinct()
        )
        for notification_id in notification_ids:
            result = notify_gateway.get_notification_by_id(
                notification_id,
                notify_service_name=NotifyServiceName.investment,
            )
            if 'status' in result:
                NoRecentExportInteractionReminder.all_objects.filter(
                    email_notification_id=notification_id,
                ).update(
                    email_delivery_status=result['status'],
                    modified_on=now(),
                )


def update_notify_email_delivery_status_for_new_export_interaction():
    if not is_feature_flag_active(
        EXPORT_NEW_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    ):
        logger.info(
            f'Feature flag {EXPORT_NEW_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME}'
            ' is not active, exiting.',
        )
        return

    with advisory_lock(
        'update_new_export_interaction_email_delivery',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Email status checks for new export interaction are already '
                'being processed by another worker.',
            )
            return
        current_date = now()
        date_threshold = current_date - relativedelta(days=4)

        notification_ids = (
            NewExportInteractionReminder.all_objects.filter(
                Q(email_delivery_status=EmailDeliveryStatus.UNKNOWN)
                | Q(email_delivery_status=EmailDeliveryStatus.SENDING),
                created_on__gte=date_threshold,
                email_notification_id__isnull=False,
            )
            .values_list('email_notification_id', flat=True)
            .distinct()
        )
        for notification_id in notification_ids:
            result = notify_gateway.get_notification_by_id(
                notification_id,
                notify_service_name=NotifyServiceName.investment,
            )
            if 'status' in result:
                NewExportInteractionReminder.all_objects.filter(
                    email_notification_id=notification_id,
                ).update(
                    email_delivery_status=result['status'],
                    modified_on=now(),
                )


def update_notify_email_delivery_status_for_no_recent_interaction():
    if not is_feature_flag_active(
        INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME,
    ):
        logger.info(
            f'Feature flag {INVESTMENT_NO_RECENT_INTERACTION_REMINDERS_EMAIL_STATUS_FLAG_NAME}'
            ' is not active, exiting.',
        )
        return

    with advisory_lock(
        'update_no_recent_interaction_email_delivery',
        wait=False,
    ) as acquired:
        if not acquired:
            logger.info(
                'Email status checks for approaching no recent interaction are already being '
                'processed by another worker.',
            )
            return
        current_date = now()
        date_threshold = current_date - relativedelta(days=4)

        notification_ids = (
            NoRecentInvestmentInteractionReminder.all_objects.filter(
                Q(email_delivery_status=EmailDeliveryStatus.UNKNOWN)
                | Q(email_delivery_status=EmailDeliveryStatus.SENDING),
                created_on__gte=date_threshold,
                email_notification_id__isnull=False,
            )
            .values_list('email_notification_id', flat=True)
            .distinct()
        )
        for notification_id in notification_ids:
            result = notify_gateway.get_notification_by_id(
                notification_id,
                notify_service_name=NotifyServiceName.investment,
            )
            if 'status' in result:
                NoRecentInvestmentInteractionReminder.all_objects.filter(
                    email_notification_id=notification_id,
                ).update(
                    email_delivery_status=result['status'],
                    modified_on=now(),
                )


def _get_active_projects(adviser):
    """
    Get active projects for given adviser.
    """
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


def _get_managed_companies(adviser):
    """
    For given adviser, get the companies for which they are the global account manager OR where
    they are a member of the one list core team
    """
    return Company.objects.filter(
        (
            (
                Q(one_list_account_owner=adviser)
                | Q(
                    pk__in=OneListCoreTeamMember.objects.filter(adviser=adviser).values(
                        'company__id',
                    ),
                )
            )
            & (
                Q(one_list_tier_id=OneListTierID.tier_d_international_trade_advisers.value)
                | Q(one_list_tier_id=OneListTierID.tier_d_overseas_post_accounts.value)
            )
        ),
    )
