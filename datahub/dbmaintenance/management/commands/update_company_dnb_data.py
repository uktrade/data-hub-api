import logging
import time

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.dnb_api.tasks import sync_company_with_dnb


logger = logging.getLogger(__name__)
API_CALLS_PER_SECOND = 1
API_CALL_INTERVAL = 1 / API_CALLS_PER_SECOND
# TODO: base these on a DRY list of fields when we add it
ALL_DNB_UPDATED_FIELDS = (
    'name',
    'trading_names',
    'address',
    'registered_address',
    'website',
    'number_of_employees',
    'is_number_of_employees_estimated',
    'turnover',
    'is_turnover_estimated',
    'website',
    'global_ultimate_duns_number',
    'company_number',
)


class CompanyNotDunsLinkedError(Exception):
    """
    Exception for when a company does not have a duns_number.
    """


class Command(CSVBaseCommand):
    """
    Command to update companies with the latest DNB data.
    """

    def __init__(self, *args, **kwargs):
        """
        Set some initial state related to API rate limiting.
        """
        self.last_called_api_time = time.perf_counter()
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        """
        Set arguments for the management command.
        """
        super().add_arguments(parser)
        parser.add_argument(
            '-f',
            '--fields',
            nargs='+',
            help='The DNBCompanySerializer fields to update.',
            required=False,
            choices=ALL_DNB_UPDATED_FIELDS,
        )

    def _limit_call_rate(self):
        """
        The method will return once enough time has elapsed to maintain the
        API_CALLS_PER_SECOND rate.
        """
        next_api_call_time = self.last_called_api_time + API_CALL_INTERVAL
        time_now = time.perf_counter()
        if time_now < next_api_call_time:
            time.sleep(next_api_call_time - time_now)
        self.last_called_api_time = time.perf_counter()

    def _process_row(self, row, simulate=False, fields=None, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)

        if not company.duns_number:
            raise CompanyNotDunsLinkedError()

        if simulate:
            return

        self._limit_call_rate()

        sync_company_with_dnb.apply(
            args=(pk, fields),
        )
