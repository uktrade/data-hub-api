from datahub.company.merge_company import merge_companies
from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid


class Command(CSVBaseCommand):
    """
    Command to company merges.
    """

    help = """
    Merging company with duns number.  This consumes a two-column CSV file from S3 which is a
    list of company IDs and Duns Number. The command will go through each company, and
    its related models, and find the company with Duns number and merge.
    """

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        source_pk = parse_uuid(row['id'])
        target_duns = row['duns']

        source_company = Company.objects.get(pk=source_pk)
        target_company = Company.objects.get(duns_number=target_duns)

        merge_companies(source_company, target_company, None)
