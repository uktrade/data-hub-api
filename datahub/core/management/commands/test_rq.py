from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.core.queues.health_check import queue_health_check
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import (
    DataHubScheduler,
    LONG_RUNNING_QUEUE,
    SHORT_RUNNING_QUEUE,
)

logger = getLogger(__name__)


class Command(BaseCommand):
    help = 'Test to see RQ can do its stuff on any environment instantly using burst worker'
    queue_name = 'test-rq-health'

    def handle(self, *args, **options):
        with DataHubScheduler('burst-no-fork') as queue:
            queue.enqueue(queue_name=self.queue_name, function=queue_health_check)
            queue.work(self.queue_name)

        job_scheduler(
            queue_name=SHORT_RUNNING_QUEUE,
            function=queue_health_check,
            is_burst=True,
            max_retries=1,
            retry_intervals=1,
        )

        job_scheduler(
            queue_name=LONG_RUNNING_QUEUE,
            function=queue_health_check,
            is_burst=True,
            max_retries=2,
            retry_intervals=[1, 2],
        )
