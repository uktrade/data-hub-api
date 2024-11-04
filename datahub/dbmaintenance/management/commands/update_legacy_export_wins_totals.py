import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.export_win.models import Win


class Command(CSVBaseCommand):
    """Command to update totals for Legacy export wins."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        export_win_id = parse_uuid(row['id'])
        total_expected_export_value = int(row['total_expected_export_value'])
        total_expected_non_export_value = int(row['total_expected_non_export_value'])
        total_expected_odi_value = int(row['total_expected_odi_value'])

        export_win = Win.objects.get(id=export_win_id)

        if not simulate:
            # The win likely will not have its original revision in the History
            with reversion.create_revision():
                reversion.add_to_revision(export_win)
                reversion.set_comment('Legacy export wins totals migration - before.')

        export_win.total_expected_export_value = total_expected_export_value
        export_win.total_expected_non_export_value = total_expected_non_export_value
        export_win.total_expected_odi_value = total_expected_odi_value

        if not simulate:
            with reversion.create_revision():
                export_win.save(
                    update_fields=(
                        'total_expected_export_value',
                        'total_expected_non_export_value',
                        'total_expected_odi_value',
                    ),
                )
                reversion.set_comment('Legacy export wins totals migration - after.')
