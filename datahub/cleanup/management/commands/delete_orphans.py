from dateutil.relativedelta import relativedelta

from datahub.cleanup.cleanup_config import ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand


ORPHAN_AGE_THRESHOLD = relativedelta(days=30 * 6)


class Command(BaseCleanupCommand):
    """
    Django command to delete orphaned records for `model`.
    Orphans are `days_before_orphaning` old records without any objects referencing them.

    If the argument `simulate=True` is passed in, the command only simulates the action.
    """

    CONFIGS = {
        'company.Contact': ModelCleanupConfig(ORPHAN_AGE_THRESHOLD),
        'company.Company': ModelCleanupConfig(ORPHAN_AGE_THRESHOLD),
        'event.Event': ModelCleanupConfig(ORPHAN_AGE_THRESHOLD, date_field='end_date')
    }
