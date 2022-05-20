from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand

from datahub.core.queue import DataHubQueue

logger = getLogger(__name__)


def queue_health_check():
    logger.info(
        f'Running RQ health check on "{datetime.now().strftime("%c")}" succeeds',
    )


class Command(BaseCommand):
    help = 'Test to see RQ can do its stuff on any environment instantly using burst worker'
    queue_name = 'test-rq-health'

    def handle(self, *args, **options):
        with DataHubQueue('burst-no-fork') as queue:
            queue.enqueue(queue_name=self.queue_name, function=queue_health_check)
            queue.work(self.queue_name)
