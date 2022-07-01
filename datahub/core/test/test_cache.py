from logging import getLogger
from threading import Thread
from time import sleep
from unittest import mock

from celery import shared_task
from pytest import fixture


from datahub.core.cache import skip_if_running
logger = getLogger(__name__)


@shared_task()
@skip_if_running(timeout=60 * 10)
def increment_task(counter=0):
    """Run task."""
    logger.info(f'Entered test_task with {counter}')
    sleep(.5)
    return counter + 1


@fixture()
def loggerpatch(monkeypatch):
    logger_patch = mock.Mock()
    monkeypatch.setattr(
        'datahub.core.test.test_cache.logger.info',
        logger_patch,
    )

    return logger_patch


def test_skip_if_running_run_function_twice_when_finished(loggerpatch):
    """NOTE: As celery in testing mode turns off async functionality,
            meaning each function will run to completion, then deleting the lock.
            Therefore this is testing this will run twice to make sure this will not
            restrict the running to only once and never again
    Args:
        loggerpatch (Mock): Patch the logger to count calls
    """
    increment_task.apply_async(args=(1,))
    increment_task.apply_async(args=(1,))

    assert loggerpatch.call_count == 2


def test_skip_if_running_should_call_once_when_run_on_multiple_threads(
    loggerpatch,
):
    Thread(target=increment_task, args=(1,)).start()
    Thread(target=increment_task, args=(1,)).start()

    assert loggerpatch.call_count == 1
