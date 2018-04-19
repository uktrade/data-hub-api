import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.utils import parse_uuid
from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update Company.headquarter_type."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--simulate',
            action='store_true',
            dest='simulate',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )
        parser.add_argument(
            '--override',
            action='store_true',
            dest='override',
            default=False,
            help='If true it will overwrite records having already set global hq.'
        )

    def _should_update(self, company, override=False):
        """Determine if we should update the company."""
        if override:
            return True

        # Assume companies with a current Global HQ are correct,
        # as this data did not come from CDMS
        return company.global_headquarters is None

    def _process_row(self, row, simulate=False, override=False, **options):
        """Process one single row."""
        company = Company.objects.get(pk=row['id'])
        global_hq = None
        global_hq_id = parse_uuid(row['global_hq_id'])
        if global_hq_id is not None:
            global_hq = Company.objects.get(pk=global_hq_id)

        if self._should_update(company, override=override):
            company.global_headquarters = global_hq

            if simulate:
                return

            with reversion.create_revision():
                company.save(
                    update_fields=(
                        'global_headquarters',
                    )
                )
                reversion.set_comment('Global HQ data migration.')
