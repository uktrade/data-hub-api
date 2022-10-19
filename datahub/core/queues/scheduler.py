from logging import getLogger

from django.conf import settings
from redis import Redis
from rq import (
    Queue as RqQueue,
    SimpleWorker,
    Worker,
)
from rq.job import Job
from rq.registry import BaseRegistry
from rq_scheduler import Scheduler


logger = getLogger(__name__)

SHORT_RUNNING_QUEUE = 'short-running'
LONG_RUNNING_QUEUE = 'long-running'


class WorkerStrategy:
    """
    Worker base facilitating connections and implementations around processing queues
    See https://python-rq.org/docs/workers/ for more information
    """

    def __init__(self, connection):
        self._connection = connection


class BurstNoFork(WorkerStrategy):
    def process_queues(self, queues, with_scheduler):
        SimpleWorker(queues, connection=self._connection).work(
            burst=True,
            with_scheduler=with_scheduler,
        )


class Fork(WorkerStrategy):
    def process_queues(self, queues, with_scheduler):
        Worker(queues, connection=self._connection).work(with_scheduler=with_scheduler)


class DataHubScheduler:
    """
    Datahub Queue utilising RQ to instantiate different types of Queues
    for processing work using Redis as the underlying PUB SUB durability layer
    """

    def __init__(
        self,
        strategy='fork',
        is_async=not settings.IS_TEST,
    ):
        self._connection = Redis.from_url(settings.REDIS_BASE_URL)
        self._scheduler = Scheduler(connection=self._connection)
        self._queues = []
        self.is_async = is_async
        self._worker_strategy = {
            'fork': Fork(self._connection),
            'burst-no-fork': BurstNoFork(self._connection),
        }[strategy]

    def enqueue(self, queue_name: str, function, *args, **kwargs):
        queue = RqQueue(
            name=queue_name,
            is_async=self.is_async,
            connection=self._connection,
        )
        self._queues.append(queue)
        return queue.enqueue(
            function,
            *args,
            **kwargs,
        )

    def cron(self, queue_name: str, cron: str, function, *args, **kwargs):
        job = self._scheduler.cron(
            cron,
            function,
            *args,
            **kwargs,
            queue_name=queue_name,
        )
        return job

    def scheduled_jobs(self):
        return self._scheduler.get_jobs()

    def queued_count(
        self,
        queue_name: str,
    ):
        queue = self.get_queue(queue_name)
        return queue.count

    def failed_count(
        self,
        queue_name: str,
    ):
        queue = self.get_queue(queue_name)
        return queue.failed_job_registry.count

    def scheduled_count(
        self,
        queue_name: str,
    ):
        queue = self.get_queue(queue_name)
        return queue.scheduled_job_registry.count

    def cron_job_count(self):
        return self._scheduler.count()

    def get_queue(self, queue_name):
        queue = RqQueue(
            name=queue_name,
            is_async=self.is_async,
            connection=self._connection,
        )

        return queue

    def cancel_cron_jobs(self):
        jobs = self._scheduler.get_jobs()
        for job in jobs:
            logger.info(f'Cancelling job {job} ...')
            result = self._scheduler.cancel(job)
            logger.info(f'Cancelled {job} {result}')
        return self.cron_job_count()

    def purge(
        self,
        queue_name: str,
        queue_state: str = 'queued',
    ):
        queue = RqQueue(
            name=queue_name,
            is_async=self.is_async,
            connection=self._connection,
        )
        if queue_state == 'queued':
            queue.empty()
            return queue.count
        if queue_state == 'failed':
            registry = queue.failed_job_registry
            return self._delete_jobs(registry)
        if queue_state == 'scheduled':
            registry = queue.scheduled_job_registry
            return self._delete_jobs(registry)

    def _delete_jobs(self, registry: BaseRegistry):
        jobs = registry.get_job_ids()
        for job in jobs:
            logger.info(f'Deleting job {job} ...')
            result = registry.remove(job, delete_job=True)
            logger.info(f'Deleted {job} {result}')
        return registry.count

    def work(self, *queues: str, with_scheduler: bool = False):
        return self._worker_strategy.process_queues(queues, with_scheduler)

    def job(self, job_id) -> Job:
        job = Job.fetch(job_id, self._connection)
        return job

    def clear(self):
        for queue in self._queues:
            queue.empty()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._connection.close()
