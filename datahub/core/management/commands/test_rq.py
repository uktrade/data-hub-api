from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.core.queues.constants import FIFTEEN_MINUTES_IN_SECONDS
from datahub.core.queues.health_check import (
    queue_health_check,
    rate_limited_queue_health_check,
    show_health_status_for_jobs,
)
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import (
    DataHubScheduler,
    LONG_RUNNING_QUEUE,
    SHORT_RUNNING_QUEUE,
)

logger = getLogger(__name__)


class Command(BaseCommand):
    help = 'Test to see RQ generates jobs verifying dedictated queues and new ones'
    queue_name = 'test-rq-health'

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--generated_jobs',
            type=int,
            help='The number of jobs to generate rate limited.',
            default=1000,
        )

    def handle(self, *args, **options):
        generated_jobs = int(options['generated_jobs'])
        with DataHubScheduler('burst-no-fork') as queue:
            queue.enqueue(queue_name=self.queue_name, function=queue_health_check)
            queue.work(self.queue_name)

        job_scheduler(
            queue_name=SHORT_RUNNING_QUEUE,
            function=queue_health_check,
            max_retries=1,
            retry_intervals=1,
        )

        job_scheduler(
            queue_name=LONG_RUNNING_QUEUE,
            function=queue_health_check,
            max_retries=2,
            retry_intervals=[1, 2],
        )
        self._simulate_rate_limited_jobs(generated_jobs)

    def _simulate_rate_limited_jobs(self, generated_jobs):
        job_ids = []
        start = datetime.utcnow()
        for _ in range(generated_jobs):
            job = job_scheduler(
                queue_name=SHORT_RUNNING_QUEUE,
                function=rate_limited_queue_health_check,
                function_kwargs={
                    'max_requests': 5,
                    'expire_in_seconds': 1,
                },
                max_retries=10,
                retry_backoff=True,
            )
            job_ids.append(job.id)
        # Schedule a check for 4 hours, checking every 15 minutes
        max_retries = 16
        job_scheduler(
            queue_name=LONG_RUNNING_QUEUE,
            function=show_health_status_for_jobs,
            function_args=(start, job_ids, f'Show status for {len(job_ids)} jobs'),
            max_retries=max_retries,
            retry_intervals=[FIFTEEN_MINUTES_IN_SECONDS] * max_retries,
        )
