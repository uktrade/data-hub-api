from datetime import datetime
from functools import reduce
from logging import getLogger
from operator import concat
from time import sleep

from django.conf import settings
from redis import Redis
from redis_rate_limit import RateLimit
from rq import Worker
from rq.exceptions import NoSuchJobError

from datahub.core.queues.errors import RetryError
from datahub.core.queues.scheduler import (
    DataHubScheduler,
    LONG_RUNNING_QUEUE,
    SHORT_RUNNING_QUEUE,
)


logger = getLogger(__name__)


class CheckRQWorkers:
    """Check that RQs are up and running."""

    name = 'running-queue-workers'
    expected_worker_names = [SHORT_RUNNING_QUEUE, LONG_RUNNING_QUEUE]

    def check(self):
        """Perform the check."""
        redis = Redis.from_url(settings.REDIS_BASE_URL)
        workers = Worker.all(connection=redis)
        queues = [worker.queue_names() for worker in workers]
        queue_names = reduce(concat, queues, [])
        missing_queues = set(self.expected_worker_names) - set(queue_names)
        if missing_queues:
            return False, f'RQ queue(s) not running: {missing_queues}'
        return True, ''


def queue_health_check():
    logger.info(
        f'Running RQ health check on "{datetime.now().strftime("%c")}" succeeds',
    )


def rate_limited_queue_health_check(max_requests=5, expire_in_seconds=1):
    with RateLimit(
        resource='rate_limited_queue_health_check',
        client='localhost',
        max_requests=max_requests,
        expire=expire_in_seconds,
        redis_pool=Redis.from_url(settings.REDIS_BASE_URL).connection_pool,
    ):
        sleep(0.050)
        queue_health_check()


def show_health_status_for_jobs(
    start_time,
    job_ids,
    description='Show status of jobs',
):
    status = {
        'success_count': 0,
        'failure_count': 0,
    }
    scheduler = DataHubScheduler()
    for job_id in job_ids:
        try:
            job = scheduler.job(job_id=job_id)
            if job.is_finished:
                status['success_count'] += 1
            elif job.is_failed:
                status['failure_count'] += 1
            else:
                error_message = f'{job_id} has a "{job.get_status(refresh=False)}" status'
                raise RetryError(error_message)
        except NoSuchJobError:
            # Job success ttl expired and assumed to have succeeded
            status['success_count'] += 1

    success_count, failure_count = (
        status['success_count'],
        status['failure_count'],
    )
    logger.info(
        f'{description} rate_limited_health_check started at '
        f'"{start_time.strftime("%m/%d/%Y, %H:%M:%S")}" and ending at '
        f'{datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")}: '
        f'succeeded to update {success_count},'
        f'failed to update: {failure_count}',
    )
