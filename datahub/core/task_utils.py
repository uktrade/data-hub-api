from contextlib import contextmanager

from celery.five import monotonic
from django.core.cache import cache


@contextmanager
def acquire_lock(lock_id, lock_expiry):
    """
    Context manager to acquire a lock with the specified identifier and expiry.

    Args:
      * lock_id - string - the identifier for the lock
      * lock_expiry - int - the time in seconds before the lock should expire

    Returns:
      True if the lock was acquired successfully, False otherwise.

    """
    timeout_at = monotonic() + lock_expiry - 3
    acquired = cache.add(lock_id, '', lock_expiry)
    try:
        yield acquired
    finally:
        not_yet_expired = monotonic() < timeout_at
        if acquired and not_yet_expired:
            cache.delete(lock_id)
