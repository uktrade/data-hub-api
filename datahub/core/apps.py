import atexit

from django.apps import AppConfig

from datahub.core.thread_pool import shut_down_thread_pool


class CoreConfig(AppConfig):
    """Configuration class for this app."""

    name = 'datahub.core'

    def ready(self):
        """Registers an atexit handler to (cleanly) shut down the thread pool.

        I haven't found a better way to do this; this won't get called when using runserver_plus,
        but will be when using gunicorn.
        """
        atexit.register(shut_down_thread_pool)
