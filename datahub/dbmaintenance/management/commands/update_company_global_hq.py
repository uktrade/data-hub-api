import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.utils import parse_uuid
from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update Company.global_headquarters."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--overwrite',
            action='store_true',
            default=False,
            help='If true it will overwrite all provided records.'
        )

    def _should_update(self, company, overwrite=False):
        """Determine if we should update the company."""
        if overwrite:
            return True

        # Assume companies with a current Global HQ are correct,
        # as this data did not come from CDMS
        return company.global_headquarters is None

    def _process_row(self, row, simulate=False, overwrite=False, **options):
        """Process one single row."""
        company = Company.objects.get(pk=parse_uuid(row['id']))
        global_hq_id = parse_uuid(row['global_hq_id'])

        if self._should_update(company, overwrite=overwrite):
            company.global_headquarters_id = global_hq_id

            if simulate:
                return

            with reversion.create_revision():
                company.save(
                    update_fields=(
                        'global_headquarters',
                    )
                )
                reversion.set_comment('Global HQ data correction.')
