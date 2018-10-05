import reversion

from datahub.company.models import Company
from datahub.company.serializers import CompanySerializer
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


class Command(CSVBaseCommand):
    """Command to update Company.global_headquarters."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--overwrite',
            action='store_true',
            default=False,
            help='If true it will overwrite all provided records.',
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

        if self._should_update(company, overwrite=overwrite):
            global_hq_id = parse_uuid(row['global_hq_id'])
            global_hq = {
                'id': global_hq_id,
            } if global_hq_id is not None else None

            data = {
                'global_headquarters': global_hq,
            }

            serializer = CompanySerializer(
                instance=company,
                data=data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            if simulate:
                return

            with reversion.create_revision():
                serializer.validated_data['modified_by'] = None
                serializer.save()
                reversion.set_comment('Global HQ data correction.')
