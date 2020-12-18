from django.db.models import Q

from datahub.cleanup.cleanup_config import ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand
from datahub.metadata.models import Team


class DummyFilter(object):
    """
    Just a dummy filter to satisfy the
    :class:`datahub.cleanup.cleanup_config.ModelCleanupConfig` constructor,
    which is expecting a list where the first item is an instance of
    :class:`datahub.cleanup.cleanup_config.DatetimeLessThanCleanupFilter`,
    which doesn't make sense with
    :class:`datahub.metadata.models.Team`.

    This class just implements the minimal required interface.
    """

    date_field = 'disabled_on'

    @staticmethod
    def as_q():
        """Returns an empty query"""
        return Q()


class Command(BaseCleanupCommand):
    """Deletes all orphaned :class:`datahub.metadata.models.Team` records"""

    model_name = 'metadata.Team'
    CONFIGS = {'metadata.Team': ModelCleanupConfig([DummyFilter()])}

    def add_arguments(self, parser):
        """Override to add the ``list-only`` argument"""
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '-l',
            '--list-only',
            action='store_true',
            help='List team IDs which will be deleted by the command',
        )

    def handle(self, *args, list_only, **options):
        """Override to add the ``list-only`` argument"""
        if list_only:
            for item in self._get_query(Team):
                self.stdout.write(str(item.id))
        else:
            super(Command, self).handle(*args, **options)
