import os

from logging import getLogger

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.conf import settings

from datahub.core.queues.constants import EVERY_HOUR, EVERY_TEN_MINUTES
from datahub.core.queues.health_check import queue_health_check
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.search.tasks import sync_all_models
logger = getLogger(__name__)


def schedule_jobs():
    logger.info('Scheduling jobs that run on a cron')
    job_scheduler(
        function=queue_health_check,
        cron=EVERY_TEN_MINUTES,
    )

    if settings.ENABLE_DAILY_OPENSEARCH_SYNC:
        job_scheduler(
            function=sync_all_models,
            cron=EVERY_HOUR,
        )


def create_rqscheduler_command():
    command = f'rqscheduler --url {settings.REDIS_BASE_URL} --verbose --interval 60'
    return command


schedule_jobs()
os.system(create_rqscheduler_command())
