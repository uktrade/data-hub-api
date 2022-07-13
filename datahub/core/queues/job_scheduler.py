from logging import getLogger

from django.conf import settings
from rq import Retry

from datahub.core.queues.queue import DataHubQueue, SHORT_RUNNING_QUEUE, TEST_PREFIX

logger = getLogger(__name__)


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
        job = queue.enqueue(
            queue_name=queue_name,
            function=function,
            args=function_args,
            kwargs=function_kwargs,
            retry=Retry(
                max=max_retries,
                interval=retry_intervals,
            ),
        )
        logger.info(f'Generated job id "{job.id}" with "{job.__dict__}"')
        if settings.IS_TEST:
            queue.work(queue_name)
        return job


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
