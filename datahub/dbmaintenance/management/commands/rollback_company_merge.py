from datahub.company.merge_company import rollback_merge_companies
from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


class Command(CSVBaseCommand):
    """
    Command to rollback company merges.
    """

    help = """
    Rollback company merges.  This consumes a one-column CSV file from S3 which is a
    list of company IDs to rollback. The command will go through each company, and
    its related models, and reinstate them to how they were before the merge.
    """

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        former_source_company = Company.objects.get(pk=pk)

        if simulate:
            return

        rollback_merge_companies(former_source_company)
