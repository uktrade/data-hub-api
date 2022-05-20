from logging import getLogger

from django.conf import settings
from redis import Redis
from rq import (
    Queue as RqQueue,
    Retry,
    SimpleWorker,
    Worker,
)

logger = getLogger(__name__)

SHORT_RUNNING_QUEUE = 'short-running'
LONG_RUNNING_QUEUE = 'long-running'
TEST_PREFIX = 'test-'
TEST_SHORT_RUNNING_QUEUE = TEST_PREFIX + SHORT_RUNNING_QUEUE
TEST_LONG_RUNNING_QUEUE = TEST_PREFIX + LONG_RUNNING_QUEUE


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
        queue = RqQueue(
            queue_name,
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


def job_scheduler(
    function,
    function_args=None,
    function_kwargs=None,
    max_retries=3,
    queue_name=SHORT_RUNNING_QUEUE,
    is_burst=False,
    retry_backoff=False,
    retry_intervals=0,
):
    """Job Scheduler for setting up Jobs that run tasks

    Args:
        function (function): Any function or task definition that can be executed
        function_args (*args, optional): Function argument values. Defaults to None.
        function_kwargs (**kwargs, optional): Function key value arguments. Defaults to None.
        max_retries (int, optional): Maximum number of retries before giving up.
            Defaults to 3 based on the RQ default.
        queue_name (string, optional): Name of a queue to schedule work with. Defaults to
        SHORT_RUNNING_QUEUE.
        is_burst (bool, optional): If True, will use a burst worker queue strategy.
            If False, will use the default queue strategy running a fetch-fork-execute loop.
            Defaults to False.
        retry_backoff (bool or int, optional): If True, will create an exponential backoff list of
            intervals based on the amount of max_retries configured starting from the first second.
            If False, will leave the retry intervals at the defaulted 0.
            If assigned a value, will start from the value assigned.
            Defaults to False.
        retry_intervals (int or [int], optional): Interval between retries in seconds.
            Can assign a retry jitter list [30,60,90] or a list of explicit exponential
            backoff values, like what is generated in retry_backoff, but manually assigned.
            You can also assign a single valued integer, that will be repeated for the
            retry amount.
            Defaults to 0.
    """
    if settings.IS_TEST:
        queue_name = TEST_PREFIX + queue_name
        is_burst = True

    retry_intervals = calculate_retry_intervals(
        max_retries,
        retry_intervals,
        retry_backoff,
    )

    logger.info(
        f"Configuring RQ with function '{function}' function args/kwargs '{function_args}' "
        f"'{function_kwargs}' retries '{max_retries}' with queue '{queue_name}' "
        f"retry intervals '{retry_intervals}'",
    )
    with DataHubQueue('burst-no-fork' if is_burst else 'fork') as queue:
        queue.enqueue(
            queue_name=queue_name,
            function=function,
            args=function_args,
            kwargs=function_kwargs,
            retry=Retry(
                max=max_retries,
                interval=retry_intervals,
            ),
        )
        if settings.IS_TEST:
            queue.work(queue_name)


def calculate_retry_intervals(
    max_retries: int,
    retry_intervals: list | int,
    retry_backoff: bool | int,
):
    is_retry_backoff_value_valid = isinstance(retry_backoff, int) and retry_backoff > 1
    if (retry_backoff is True or is_retry_backoff_value_valid) and max_retries > 0:
        exponential_intervals = []
        start = 1
        if is_retry_backoff_value_valid:
            exponential_intervals.append(int(retry_backoff))
            start = int(retry_backoff) + 1
        shift_range_by_start = max_retries + start
        for interval in range(start, shift_range_by_start):
            exponential_intervals.append(interval ** 2)
        return exponential_intervals[0:max_retries]
    return retry_intervals
