import logging
import os

from celery import Celery
from celery.signals import after_setup_logger
from celery.utils.serialization import strtobool
from celery.worker.control import inspect_command


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('datahub')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@after_setup_logger.connect
def after_setup_logger_handler(**kwargs):
    """As the Elasticsearch module is noisy, set its log level to WARNING for Celery workers."""
    es_logger = logging.getLogger('elasticsearch')
    es_logger.setLevel(logging.WARNING)


@inspect_command(
    alias='dump_conf',
    signature='[include_defaults=False]',
    args=[('with_defaults', strtobool)],
)
def conf(state, with_defaults=False, **kwargs):
    """
    This overrides the default `conf` inspect command to effectively disable it.

    This is to stop sensitive configuration information appearing in e.g. Flower.

    (Celery makes an attempt to remove sensitive information, but it is not foolproof.)
    """
    return {'error': 'Config inspection has been disabled.'}
