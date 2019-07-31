from urllib.error import URLError

from celery.utils.log import get_task_logger
from django.conf import settings
from prometheus_client import push_to_gateway as _push_to_gateway

from datahub.monitoring import registry


logger = get_task_logger(__name__)


def push_to_gateway(job):
    """
    Wrapper around push_to_gateway that handles the exceptions gracefully.
    """
    pushgateway_url = settings.PUSHGATEWAY_URL
    if pushgateway_url is None:
        logger.info('PUSHGATEWAY_URL has not been configured.')
        return
    try:
        _push_to_gateway(pushgateway_url, job=job, registry=registry)
    except URLError:
        logger.info(f'Cannot reach Pushgateway at: {pushgateway_url}')
