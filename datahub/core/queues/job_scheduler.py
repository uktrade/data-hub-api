from logging import getLogger
from typing import Literal

from rq import Retry

from datahub.core.queues.constants import THREE_MINUTES_IN_SECONDS
from datahub.core.queues.scheduler import DataHubScheduler, SHORT_RUNNING_QUEUE

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
    cron=None,
    time_delta=None,
    job_timeout=THREE_MINUTES_IN_SECONDS,
    description=None,
):
    """Job scheduler for setting up Jobs that run tasks

    Args:
        function (function): Any function or task definition that can be executed
        function_args (*args, optional): Function argument values. Defaults to None.
        function_kwargs (**kwargs, optional): Function key value arguments. Defaults to None.
        max_retries (int, optional): Maximum number of retries before giving up.
            If None, the function will not retry.
            Defaults to 3 based on the RQ default.
        queue_name (string, optional): Name of a queue to schedule work with. Defaults to
            SHORT_RUNNING_QUEUE.
        is_burst (bool, optional): If True, will use a burst worker queue strategy.
            If False, will use the default queue strategy running a fetch-fork-execute loop
            or a blocking worker process that will run and block until terminated.
            Defaults to False unless this is a Test.
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
        cron (str, optional): Add a schedule using the cron format, see https://crontab.cronhub.io/
            for generating a cron string. Cannot be used if time_delta is defined.
        time_delta (datetime.timedelta, optional): Schedules the job to run at
            X seconds/minutes/hours/days/weeks later. Cannot be used if cron is defined.
        job_timeout (int, optional): Default timeout is 180 seconds
        description (str, opional): Cron scheduling allows a description to be assigned making it
            easier for debugging and tracing cron jobs, and is only applicable to jobs with crons
    """
    is_backoff_an_int = isinstance(retry_backoff, int) and retry_backoff > 1
    if retry_backoff is True or is_backoff_an_int:
        retry_intervals = retry_backoff_intervals(max_retries, retry_backoff, is_backoff_an_int)
    else:
        retry_intervals = retry_intervals

    if cron is not None and time_delta is not None:
        raise Exception('cron and time_delta can not both be defined.')

    logger.info(
        f"Configuring RQ with function '{function}' function args/kwargs '{function_args}' "
        f"'{function_kwargs}' retries '{max_retries}' with queue '{queue_name}' "
        f"retry intervals '{retry_intervals}'",
    )
    with DataHubScheduler(
        strategy='burst-no-fork' if is_burst else 'fork',
    ) as scheduler:
        if cron is not None:
            job = scheduler.cron(
                queue_name=queue_name,
                cron=cron,
                function=function,
                args=function_args,
                kwargs=function_kwargs,
                description=description,
            )
        else:
            retry = None
            if max_retries is not None:
                retry = Retry(
                    max=max_retries,
                    interval=retry_intervals,
                )
            if time_delta is not None:
                job = scheduler.enqueue_in(
                    queue_name=queue_name,
                    time_delta=time_delta,
                    function=function,
                    args=function_args,
                    kwargs=function_kwargs,
                    retry=retry,
                    job_timeout=job_timeout,
                )
            else:
                job = scheduler.enqueue(
                    queue_name=queue_name,
                    function=function,
                    args=function_args,
                    kwargs=function_kwargs,
                    retry=retry,
                    job_timeout=job_timeout,
                )
        logger.info(f'Generated job id "{job.id}" with "{job.__dict__}"')
        return job


def retry_backoff_intervals(
    max_retries: int,
    retry_backoff: bool | int,
    is_backoff_an_int: bool,
) -> (list | Literal[0]):
    if retry_backoff is True or is_backoff_an_int:
        start = 1 if not is_backoff_an_int else int(retry_backoff)
        return exponential_backoff_intervals(max_retries, start)
    return 0


def exponential_backoff_intervals(
    max_retries: int,
    start: int,
) -> list:
    result = [start]
    for interval in range(start + 1, start + max_retries):
        result.append(interval ** 2)
    return result
