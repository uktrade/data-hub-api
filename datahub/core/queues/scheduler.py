from logging import getLogger

from django.conf import settings
from redis import Redis
from rq import (
    Queue as RqQueue,
    SimpleWorker,
    Worker,
)
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

    def get_scheduled_jobs(self):
        return self._scheduler.get_jobs()

    def work(self, *queues: str, with_scheduler: bool = False):
        return self._worker_strategy.process_queues(queues, with_scheduler)

    def clear(self):
        for queue in self._queues:
            queue.empty()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._connection.close()
