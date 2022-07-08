from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.core.queue import DataHubQueue, job_scheduler, LONG_RUNNING_QUEUE, SHORT_RUNNING_QUEUE

logger = getLogger(__name__)


def queue_health_check():
    logger.info(
        f'Running RQ health check on "{datetime.now().strftime("%c")}" succeeds',
    )


class Command(BaseCommand):
    help = 'Test to see RQ can do its stuff on any environment instantly using burst worker'
    queue_name = 'test-rq-health'

    def handle(self, *args, **options):
        with DataHubQueue('burst-no-fork') as queue:
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
