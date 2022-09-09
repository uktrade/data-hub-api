from logging import getLogger
from pprint import pprint

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
CRON_QUEUE = 'cron-running'

class WorkerStrategy:
    """
    Worker base facilitating connections and implementations around processing queues
    See https://python-rq.org/docs/workers/ for more information
    """

    def __init__(self, connection):
        self._connection = connection


class BurstNoFork(WorkerStrategy):
    def process_queues(self, queues):
        SimpleWorker(queues, connection=self._connection).work(burst=True)


class Fork(WorkerStrategy):
    def process_queues(self, queues):
        Worker(queues, connection=self._connection).work()


class DataHubQueue:
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
        self._queues = []
        self.is_async = is_async
        self._worker_strategy = {
            'fork': Fork(self._connection),
            'burst-no-fork': BurstNoFork(self._connection),
        }[strategy]
    

    def enqueue(self, queue_name: str, function, *args, **kwargs):
        def cron_test_function():
            pprint('######################')
            pprint('testing cron successful')

        pprint('en here ###############')
        # test_queue = RqQueue(name=CRON_QUEUE, is_async=self.is_async, connection=Redis())
        
        scheduler = Scheduler(CRON_QUEUE, connection=Redis.from_url(settings.REDIS_BASE_URL))
        scheduler.cron('* * * * *', cron_test_function, repeat=10)
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

    def work(self, *queues: str):
        return self._worker_strategy.process_queues(queues)

    def clear(self):
        for queue in self._queues:
            queue.empty()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._connection.close()
