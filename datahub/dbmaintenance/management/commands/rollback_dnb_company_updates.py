from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.dnb_api.utils import rollback_dnb_company_update


class Command(CSVBaseCommand):
    """
    Command to rollback company updates made from DNB data.
    """

    help = """
    Rollback company updates made from DNB data.  This consumes a one-column CSV file from S3 which
    is a list of company IDs to rollback as well as an update descriptor string.  The command will
    go through each company to rollback and will re-instate the fields updated by D&B.
    """

    def add_arguments(self, parser):
        """
        Set arguments for the management command.
        """
        super().add_arguments(parser)
        parser.add_argument(
            '-d',
            '--update-descriptor',
            help='The descriptor for the reversion version to rollback.',
            required=True,
            type=str,
        )

    def _process_row(self, row, update_descriptor, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)

        if simulate:
            return

        rollback_dnb_company_update(company, update_descriptor)
