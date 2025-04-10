from dateutil.relativedelta import relativedelta

from datahub.cleanup.cleanup_config import DatetimeLessThanCleanupFilter, ModelCleanupConfig
from datahub.cleanup.management.commands._base_command import BaseCleanupCommand
from datahub.company.models import Company, Contact

ORPHAN_AGE_THRESHOLD = relativedelta(months=6)


class Command(BaseCleanupCommand):
    """Django command to delete orphaned records for `model`.
    Orphans are `days_before_orphaning` old records without any objects referencing them.

    If the argument `simulate=True` is passed in, the command only simulates the action.

    Only one filter is currently supported for each configuration specified in CONFIGS,
    and relation filters are also not supported. If these are needed, the tests need to be
    updated to account for such scenarios.
    """

    CONFIGS = {
        'company.Contact': ModelCleanupConfig(
            (DatetimeLessThanCleanupFilter('modified_on', ORPHAN_AGE_THRESHOLD),),
            excluded_relations=(
                Contact._meta.get_field('wins'),
                Contact._meta.get_field('great_export_enquiries'),
                Contact._meta.get_field('stova_attendee'),
            ),
        ),
        'company.Company': ModelCleanupConfig(
            (DatetimeLessThanCleanupFilter('modified_on', ORPHAN_AGE_THRESHOLD),),
            # We want to delete the relations below along with any orphaned companies
            excluded_relations=(
                Company._meta.get_field('company_list_items'),
                Company._meta.get_field('export_countries'),
                Company._meta.get_field('export_countries_history'),
                Company._meta.get_field('great_export_enquiries'),
                Company._meta.get_field('stova_attendee'),
                Company._meta.get_field('pipeline_list_items'),
                Company._meta.get_field('new_export_interaction_reminders'),
                Company._meta.get_field('no_recent_export_interaction_reminders'),
                Company._meta.get_field('wins'),
                Company._meta.get_field('task_company'),
            ),
        ),
        'event.Event': ModelCleanupConfig(
            (DatetimeLessThanCleanupFilter('end_date', relativedelta(months=18)),),
        ),
    }
