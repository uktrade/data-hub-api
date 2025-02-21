from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.duns_number."""

    additional_logging: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.additional_logging = {
            'errors': [],
            'duplicate_company_already_merged_with_target': 0,
            'duplicate_company_already_merged': 0,
        }

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        duns_number = parse_limited_string(row['duns_number'], blank_value=None)

        if company.duns_number == duns_number:
            return

        company.duns_number = duns_number

        target_company = Company.objects.filter(duns_number=duns_number).first()
        if target_company and self.is_source_already_merged_into_target(company, target_company):
            return

        if self.is_source_already_merged(company):
            return

        if simulate:
            return

        try:
            with reversion.create_revision():
                company.save(update_fields=('duns_number',))
                reversion.set_comment('Duns number updated.')
        except Exception as error:
            self.additional_logging['errors'].append(
                {
                    'id': pk,
                    'duns_number': duns_number,
                    'error': error,
                },
            )
            raise error

    def is_source_already_merged_into_target(self, company: Company, target_company: str) -> bool:
        """
        Checks if the source has already been merged into another company with the target duns
        number. These companies should not have the duns number updated as they have been marked
        as a duplicate and merged into another company with that company having the correct duns
        number.

        :returns: True if the source company has already been merged into a company with the target
            duns numbers. False otherwise.
        """
        if company.transferred_to_id != target_company.id:
            return False
        self.additional_logging['duplicate_company_already_merged_with_target'] += 1
        return True

    def is_source_already_merged(self, company: Company) -> bool:
        """
        Checks if the source has already been merged into another company. These companies should
        not have the duns number updated as they have been marked as a duplicate and merged into
        another company.

        :returns: True if the source company has already been merged into a company. False
            otherwise.
        """
        if not company.transferred_to_id:
            return False
        self.additional_logging['duplicate_company_already_merged'] += 1
        return True

    def handle(self, *args, **options):
        """
        Process the CSV file and logs some additional logging to help with the company duns update.
        """
        super().handle(*args, **options)
        logger.info('Errors:')
        logger.info(self.additional_logging)
        logger.info(f'{self.additional_logging["errors"]}')
        logger.info(
            'Total companies already merged with a company matching target duns: '
            f'{self.additional_logging["duplicate_company_already_merged_with_target"]}',
        )
        logger.info(
            'Total companies already merged and not updated: '
            f'{self.additional_logging["duplicate_company_already_merged_with_target"]}',
        )
        self.additional_logging.clear()
