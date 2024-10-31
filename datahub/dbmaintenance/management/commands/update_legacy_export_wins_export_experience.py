import reversion

from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.export_win.models import Win


class Command(CSVBaseCommand):
    """Command to update export experience for Legacy export wins."""

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        export_win_id = parse_uuid(row['export_win_id'])
        export_experience_id = row['export_experience_id']

        export_win = Win.objects.get(id=export_win_id)

        if export_win.export_experience_id == export_experience_id:
            return

        if not simulate:
            # The win likely will not have its original revision in the History
            with reversion.create_revision():
                reversion.add_to_revision(export_win)
                reversion.set_comment('Legacy export wins export experience migration - before.')

        export_win.export_experience_id = export_experience_id

        if not simulate:
            with reversion.create_revision():
                export_win.save(
                    update_fields=(
                        'export_experience_id',
                    ),
                )
                reversion.set_comment('Legacy export wins export experience migration - after.')
