from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)


def queue_health_check():
    logger.info(
        f'Running RQ health check on "{datetime.now().strftime("%c")}" succeeds',
    )
