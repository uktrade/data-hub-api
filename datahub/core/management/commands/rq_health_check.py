import sys

from functools import reduce
from logging import getLogger
from operator import concat

from django.conf import settings
from django.core.management.base import BaseCommand
from redis import Redis
from rq import Worker


logger = getLogger(__name__)


class Command(BaseCommand):
    help = 'RQ Health Check'

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--queue',
            type=str,
            help='Name of the queue to perform health check on.',
        )

    def handle(self, *args, **options):
        if options['queue']:
            queue = str(options['queue'])
            redis = Redis.from_url(settings.REDIS_BASE_URL)
            workers = Worker.all(connection=redis)
            queue_names = reduce(concat, [worker.queue_names() for worker in workers], [])
            missing_queues = set([queue]) - set(queue_names)

            if missing_queues:
                logger.error(f'RQ queue not running: {missing_queues}')
                sys.exit(1)
            logger.info('OK')
            sys.exit(0)

        logger.error('Nothing checked! Please provide --queue parameter')
        sys.exit(1)
