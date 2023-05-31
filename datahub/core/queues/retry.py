import time
from logging import getLogger
from typing import Callable, TypeVar
logger = getLogger(__name__)
T = TypeVar('T')


def retry_with_backoff(
    fn: Callable[[], T],
    retries=5,
    backoff_in_seconds=1,
) -> T:
    count = 0
    while True:
        try:
            return fn()
        except Exception:
            if count == retries:
                raise
        sleep = (backoff_in_seconds * 2 ** count)
        logger.info(f'Waiting to retry after {sleep} seconds')
        time.sleep(sleep)
        count += 1
