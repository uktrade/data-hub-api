import os

from logging import getLogger

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings

from datahub.company.tasks.company import schedule_automatic_company_archive
from datahub.company.tasks.contact import schedule_automatic_contact_archive
from datahub.core.queues.constants import (
    EVERY_EIGHT_PM_ON_SATURDAY,
    EVERY_NINE_PM_ON_SATURDAY,
    EVERY_ONE_AM,
    EVERY_SEVEN_PM,
    EVERY_TEN_MINUTES,
)
from datahub.core.queues.health_check import queue_health_check
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import DataHubScheduler
from datahub.search.tasks import sync_all_models
logger = getLogger(__name__)


def schedule_jobs():
    cancel_existing_cron_jobs()
    logger.info('Scheduling jobs that run on a cron')
    job_scheduler(
        function=queue_health_check,
        cron=EVERY_TEN_MINUTES,
    )
    job_scheduler(
        function=schedule_automatic_company_archive,
        function_kwargs={
            'limit': 20000,
            'simulate': False,
        },
        cron=EVERY_EIGHT_PM_ON_SATURDAY,
        description='Automatic Company Archive',
    )
    # The purpose of the following is to keep us posted on the backlog of
    # companies that are eligible for automatic archiving
    job_scheduler(
        function=schedule_automatic_company_archive,
        function_kwargs={
            'limit': 20000,
            'simulate': True,
        },
        cron=EVERY_SEVEN_PM,
        description='Simulate Automatic Company Archive',
    )
    job_scheduler(
        function=schedule_automatic_contact_archive,
        function_kwargs={
            'limit': 20000,
            'simulate': True,
        },
        cron=EVERY_NINE_PM_ON_SATURDAY,
        description='Simulate Automatic Contact Archive',
    )

    if settings.ENABLE_DAILY_OPENSEARCH_SYNC:
        job_scheduler(
            function=sync_all_models,
            cron=EVERY_ONE_AM,
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
