from logging import getLogger

from django.core.management import BaseCommand

from datahub.core.queues.scheduler import DataHubScheduler

logger = getLogger(__name__)

SUPPORTED_QUEUE_NAMES = ['long-running', 'short-running', 'test-rq-health']
SUPPORTED_QUEUE_STATES = ['queued', 'failed']


class Command(BaseCommand):
    """Purge any queue based on arguments."""

    help = """Purge queues on different states/registries."""
    requires_migrations_checks = True

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            'queue_name',
            type=str,
            help=f'The Name of a queue to purge, [{SUPPORTED_QUEUE_NAMES}].',
            choices=SUPPORTED_QUEUE_NAMES,
        )
        parser.add_argument(
            '--queue_state',
            type=str,
            default='queued',
            help=f'Queue types refer to [{SUPPORTED_QUEUE_STATES}]',
            choices=SUPPORTED_QUEUE_STATES,
        )

    def handle(self, *args, **options):
        queue_name = options['queue_name'].lower()
        queue_state = options['queue_state'].lower()

        logger.info(f'Ready to purge the "{queue_state}" "{queue_name}" queue ...')
        self.purge(queue_name, queue_state)

        msg = f'Successfully purged {queue_state} on {queue_name} queue'
        return self.style.SUCCESS(msg)

    def purge(self, queue_name: str, queue_state: str):
        with DataHubScheduler() as scheduler:
            scheduler.purge(queue_name, queue_state)
