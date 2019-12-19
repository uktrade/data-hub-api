import logging
import time

from django.utils.timezone import now

from datahub.company.models import Company
from datahub.core.utils import log_to_sentry
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.dnb_api.constants import ALL_DNB_UPDATED_FIELDS
from datahub.dnb_api.tasks import sync_company_with_dnb


logger = logging.getLogger(__name__)
API_CALLS_PER_SECOND = 1
API_CALL_INTERVAL = 1 / API_CALLS_PER_SECOND


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
        self.start_timestamp = now().isoformat(timespec='seconds')
        self.update_descriptor = f'command:update_company_dnb_data:{self.start_timestamp}'
        self.success_count = 0
        self.processed_count = 0
        self.processed_ids = []
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        """
        Override handle method to add some audit logging.
        """
        super().handle(*args, **options)
        if not options['simulate']:
            self._record_audit_log()

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

    def _record_audit_log(self):
        audit = {
            'success_count': self.success_count,
            'failure_count': self.processed_count - self.success_count,
            'updated_company_ids': self.processed_ids,
            'start_time': self.start_timestamp,
            'end_time': now().isoformat(timespec='seconds'),
        }
        log_to_sentry('update_company_dnb_data command completed.', extra=audit)

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
        self.processed_count += 1
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)

        if not company.duns_number:
            raise CompanyNotDunsLinkedError()

        if simulate:
            return

        self._limit_call_rate()

        sync_company_with_dnb.apply(
            args=(pk, fields, self.update_descriptor),
            throw=True,
        )
        self.processed_ids.append(pk)
        self.success_count += 1
