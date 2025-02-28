from logging import getLogger

from datahub.company.merge_company import merge_companies
from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to company merges.
    """

    help = """
    Merging company with duns number.  This consumes a two-column CSV file from S3 which is a
    list of company IDs and Duns Number. The command will go through each company, and
    its related models, and find the company with Duns number and merge.
    """

    additional_logging: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.additional_logging = {
            'companies_with_subsidiaries': [],
            'target_companies_archived': [],
            'source_company_global_headquarters': [],
        }

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        source_pk = parse_uuid(row['id'])
        target_duns = row['duns']

        source_company = Company.objects.get(pk=source_pk)
        target_company = Company.objects.get(duns_number=target_duns)

        if source_company.subsidiaries.exists():
            self.additional_logging['companies_with_subsidiaries'].append(str(source_company.id))
        if target_company.archived:
            self.additional_logging['target_companies_archived'].append(str(target_company.id))
        if source_company.global_headquarters:
            self.additional_logging['source_company_global_headquarters'].append(
                str(source_company.id))
        merge_companies(source_company, target_company, None)

    def handle(self, *args, **options):
        """
        Process the CSV file and logs some additional logging to help with companies merging
        """
        super().handle(*args, **options)
        logger.info(
            'List of Source Companies with Subsidiaries: '
            f'{self.additional_logging["companies_with_subsidiaries"]}')
        logger.info(
            'List of Target Companies Archived: '
            f'{self.additional_logging["target_companies_archived"]}')
        logger.info(
            'List of Source Compnies with Global Headqaurters: '
            f'{self.additional_logging["source_company_global_headquarters"]}')

        self.additional_logging.clear()
