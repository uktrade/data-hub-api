from dateutil.relativedelta import relativedelta

from datahub.cleanup.cleanup_config import ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand


class Command(BaseCleanupCommand):
    """Command for deleting very old records (as per the data retention policy)."""

    help = ('Irrevocably deletes very old records for a model, using the criteria defined in the '
            'DIT Data Hub retention policy. A simulation can be performed using the --simulate '
            'argument.')

    CONFIGS = {
        # TODO: Before adding any more configurations, get_unreferenced_objects_query()
        # and BaseCleanupCommand need to be extended to allow filter conditions for related
        # models to be given.
        #
        # (Interactions does not have any dependent models, hence this has
        # not been done yet.)
        'interaction.Interaction': ModelCleanupConfig(relativedelta(years=10), 'date'),
    }
