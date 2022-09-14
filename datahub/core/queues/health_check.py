import os
from datetime import datetime
from logging import getLogger

from django.conf import settings

logger = getLogger(__name__)


def queue_health_check():
    log = f'Running RQ health check on "{datetime.now().strftime("%c")}" succeeds'
    logger.info(
        log,
    )
    if settings.DEBUG:
        log_health(log)


def log_health(log):
    with open('/tmp/test_rq.log', 'a', encoding='utf_8') as health_log:
        health_log.write(log + os.linesep)
