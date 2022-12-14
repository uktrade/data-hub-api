import os
from datetime import datetime
from logging import getLogger

import django
import environ

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings
from pytz import utc

from datahub.company.tasks.company import schedule_automatic_company_archive
from datahub.company.tasks.contact import schedule_automatic_contact_archive
from datahub.core.queues.constants import (
    EVERY_EIGHT_AM,
    EVERY_HOUR,
    EVERY_MIDNIGHT,
    EVERY_ONE_AM,
    EVERY_SEVEN_PM,
    EVERY_TEN_AM,
    EVERY_TEN_MINUTES,
    EVERY_THREE_AM_ON_TWENTY_THIRD_EACH_MONTH,
)
from datahub.core.queues.health_check import queue_health_check
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import DataHubScheduler, LONG_RUNNING_QUEUE
from datahub.dnb_api.tasks.sync import schedule_sync_outdated_companies_with_dnb
from datahub.dnb_api.tasks.update import schedule_get_company_updates
from datahub.investment.project.tasks import (
    schedule_refresh_gross_value_added_value_for_fdi_investment_projects,
)
from datahub.omis.payment.tasks import refresh_pending_payment_gateway_sessions
from datahub.reminder.tasks import (
    generate_no_recent_export_interaction_reminders,
    update_notify_email_delivery_status_for_no_recent_export_interaction,
)
from datahub.search.tasks import sync_all_models

env = environ.Env()
logger = getLogger(__name__)


def schedule_jobs():
    cancel_existing_cron_jobs()
    logger.info('Scheduling jobs that run on a cron')
    job_scheduler(
        function=queue_health_check,
        cron=EVERY_TEN_MINUTES,
    )
    job_scheduler(
        function=refresh_pending_payment_gateway_sessions,
        function_kwargs={
            'age_check': 60,  # in minutes
        },
        cron=EVERY_HOUR,
        description='Refresh pending payment gateway sessions :0',
    )
    job_scheduler(
        function=schedule_automatic_company_archive,
        function_kwargs={
            'limit': 20000,
            'simulate': False,
        },
        cron=EVERY_SEVEN_PM,
        description='Automatic Company Archive',
    )
    job_scheduler(
        function=schedule_automatic_contact_archive,
        function_kwargs={
            'limit': 20000,
            'simulate': False,
        },
        cron=EVERY_SEVEN_PM,
        description='Automatic Contact Archive',
    )
    job_scheduler(
        function=schedule_get_company_updates,
        cron=EVERY_MIDNIGHT,
        description='Update companies from dnb service',
    )
    job_scheduler(
        function=schedule_refresh_gross_value_added_value_for_fdi_investment_projects,
        cron=EVERY_THREE_AM_ON_TWENTY_THIRD_EACH_MONTH,
        description='schedule_refresh_gross_value_added_value_for_fdi_investment_projects',
    )

    if settings.ENABLE_DAILY_OPENSEARCH_SYNC:
        job_scheduler(
            function=sync_all_models,
            cron=EVERY_ONE_AM,
            description='Daily OpenSearch sync',
        )

    if settings.ENABLE_DAILY_HIERARCHY_ROLLOUT:
        dnb_modified_on_before = datetime(
            year=2019,
            month=10,
            day=24,
            hour=23,
            minute=59,
            second=59,
            tzinfo=utc,
        )
        job_scheduler(
            function=schedule_sync_outdated_companies_with_dnb,
            function_kwargs={
                'dnb_modified_on_before': dnb_modified_on_before,
                'fields_to_update': ['global_ultimate_duns_number'],
                'limit': settings.DAILY_HIERARCHY_ROLLOUT_LIMIT,
                'simulate': False,
                'max_requests': 5,
            },
            cron=EVERY_ONE_AM,
            description='dnb hierarchies backfill',
        )

    if settings.ENABLE_NO_RECENT_EXPORT_INTERACTION_REMINDERS:
        job_scheduler(
            function=generate_no_recent_export_interaction_reminders,
            max_retries=5,
            queue_name=LONG_RUNNING_QUEUE,
            retry_backoff=True,
            retry_intervals=30,
            cron=EVERY_EIGHT_AM,
            description='Daily generate no recent export interaction reminders',
        )

    if settings.ENABLE_NO_RECENT_EXPORT_INTERACTION_REMINDERS_EMAIL_DELIVERY_STATUS:
        job_scheduler(
            function=update_notify_email_delivery_status_for_no_recent_export_interaction,
            max_retries=5,
            queue_name=LONG_RUNNING_QUEUE,
            retry_backoff=True,
            retry_intervals=30,
            cron=EVERY_TEN_AM,
            description='Daily update of no recent export interaction reminder email status',
        )


def cancel_existing_cron_jobs():
    logger.info('Cancel any existing rq scheduled cron jobs')
    with DataHubScheduler() as scheduler:
        scheduler.cancel_cron_jobs()


def create_rqscheduler_command():
    command = f'rqscheduler --url {settings.REDIS_BASE_URL} --verbose --interval 60'
    return command


schedule_jobs()
os.system(create_rqscheduler_command())
