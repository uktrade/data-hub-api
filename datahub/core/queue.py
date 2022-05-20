from logging import getLogger
from urllib.parse import urlparse

from django.conf import settings
from redis import Redis
from rq import Queue as RqQueue, SimpleWorker, Worker

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

    def __init__(self, strategy='fork'):
        url = urlparse(settings.REDIS_BASE_URL)
        self._connection = Redis(
            host=url.hostname, port=url.port, db=0, password=url.password,
        )
        self._queues = []
        self._worker_strategy = {
            'fork': Fork(self._connection),
            'burst-no-fork': BurstNoFork(self._connection),
        }[strategy]

    def enqueue(self, queue_name: str, function, *args, **kwargs):
        queue = RqQueue(queue_name, connection=self._connection)
        self._queues.append(queue)
        return queue.enqueue(function, *args, **kwargs)

    def work(self, *queues: str):
        return self._worker_strategy.process_queues(queues)

    def clear(self):
        for queue in self._queues:
            queue.empty()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._connection.close()
