from dateutil.relativedelta import relativedelta

from datahub.cleanup.cleanup_config import DatetimeLessThanCleanupFilter, ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand
from datahub.company.models import Company


ORPHAN_AGE_THRESHOLD = relativedelta(months=6)


class Command(BaseCleanupCommand):
    """
    Django command to delete orphaned records for `model`.
    Orphans are `days_before_orphaning` old records without any objects referencing them.

    If the argument `simulate=True` is passed in, the command only simulates the action.

    Only one filter is currently supported for each configuration specified in CONFIGS,
    and relation filters are also not supported. If these are needed, the tests need to be
    updated to account for such scenarios.
    """

    CONFIGS = {
        'company.Contact': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('modified_on', ORPHAN_AGE_THRESHOLD),
            ),
        ),
        'company.Company': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('modified_on', ORPHAN_AGE_THRESHOLD),
            ),
            # We want to delete the relations below along with any orphaned companies
            excluded_relations=(
                Company._meta.get_field('company_list_items'),
                Company._meta.get_field('dnbmatchingresult'),
                Company._meta.get_field('unfiltered_export_countries'),
            ),
        ),
        'event.Event': ModelCleanupConfig(
            (
                DatetimeLessThanCleanupFilter('end_date', relativedelta(months=18)),
            ),
        ),
    }
