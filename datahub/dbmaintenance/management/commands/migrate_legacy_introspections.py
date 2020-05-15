from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import utc
from oauth2_provider.admin import AccessToken

from datahub.core.utils import slice_iterable_into_chunks
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.models import UserEvent

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Temporary command for creating introspection UserEvent records from legacy Django OAuth
    Toolkit AccessToken objects.

    This command should be removed once used.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument(
            '--batch-size',
            default=10_000,
            type=int,
            help='Number of objects to retrieve and create in each batch.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """
        Create introspection user events from legacy access tokens.

        This uses a transaction as it's not possible to resume it if part-complete.
        """
        batch_size = options['batch_size']

        queryset = AccessToken.objects.filter(
            user__isnull=False,
            application__isnull=True,
            scope__in=[
                'read write data-hub:internal-front-end',
                'read write introspection data-hub:internal-front-end',
            ],
            expires__lte=datetime(2020, 5, 10, tzinfo=utc),
        ).values(
            'created',
            'user_id',
        )

        insert_count = 0

        for tokens in slice_iterable_into_chunks(queryset.iterator(), batch_size):
            events = [
                UserEvent(
                    timestamp=token['created'],
                    adviser_id=token['user_id'],
                    type=UserEventType.OAUTH_TOKEN_INTROSPECTION,
                    data={'source': 'legacy_access_token'},
                )
                for token in tokens
            ]
            UserEvent.objects.bulk_create(events)
            insert_count += len(events)
            logger.info(f'{insert_count} objects processed so far...')

        logger.info(f'Command complete, {insert_count} user events created')
