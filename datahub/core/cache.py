from functools import wraps
from logging import getLogger

from django.core.cache import cache as django_cache

logger = getLogger(__name__)
cache = django_cache
FIVE_MINUTES = 60 * 5


def skip_if_running(
    timeout=FIVE_MINUTES,
    busy_message=None,
):
    def decorator_skip_if_running(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            task_name = f'{func.__module__}.{func.__name__}({args},{kwargs})'
            logger.info(task_name)
            if cache.get(task_name, False):
                busy_warning = f'{func.__name__} is busy processing'
                logger.info(busy_message if busy_message is not None else busy_warning)
                return
            else:
                cache.set(task_name, True, timeout)
            try:
                logger.info(f'Ready to process {func.__name__}')
                result = func(*args, **kwargs)
                return result
            finally:
                cache.delete(task_name)
        return wrapped

    return decorator_skip_if_running
