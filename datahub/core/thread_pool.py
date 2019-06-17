from concurrent.futures import ThreadPoolExecutor

import sentry_sdk
from django.db import close_old_connections

from datahub.core.utils import logger

_executor = ThreadPoolExecutor()


def submit_to_thread_pool(fn, *args, **kwargs):
    """Submits a function to be run in the thread pool."""
    return _submit_to_thread_pool(fn, *args, **kwargs)


def shut_down_thread_pool():
    """Shuts down the thread pool."""
    logger.info('Shutting down thread pool...')
    _executor.shutdown()


def _submit_to_thread_pool(fn, *args, **kwargs):
    """
    Implementation of submit_to_thread_pool().

    Gives tests a centralised place to patch task submission for synchronous execution.
    """
    return _executor.submit(_make_thread_pool_task(fn, *args, **kwargs))


def _make_thread_pool_task(fn, *args, **kwargs):
    """
    Wraps a task with exception handling and old- and broken-connection clean-up.

    close_old_connections() is called both before and after the execution of the task to mimic
    what Django does with requests.
    """
    def _task():
        try:
            close_old_connections()
            fn(*args, **kwargs)
        except Exception:
            msg = f'Error running thread pool task {fn.__name__}'
            logger.exception(msg)
            sentry_sdk.capture_exception()
            raise
        finally:
            close_old_connections()
    return _task
