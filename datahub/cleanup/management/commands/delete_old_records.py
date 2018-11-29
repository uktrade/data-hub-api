from dateutil.relativedelta import relativedelta

from datahub.cleanup.cleanup_config import DatetimeLessThanCleanupFilter, ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand


class Command(BaseCleanupCommand):
    """Command for deleting very old records (as per the data retention policy)."""

    help = (
        'Irrevocably deletes very old records for a model, using the criteria defined in the '
        'DIT Data Hub retention policy. A simulation can be performed using the --simulate '
        'argument.'
    )

    CONFIGS = {
        'interaction.Interaction': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('date', relativedelta(years=10)),
            ),
        ),
    }
