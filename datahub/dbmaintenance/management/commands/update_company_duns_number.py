from logging import getLogger

import reversion

from datahub.company.models import Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_limited_string, parse_uuid

logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """Command to update Company.duns_number.

    Adds additional logging to show where the duns number update would fail. The duns number is
    unique on the Company model.
    """

    additional_logging: dict

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.additional_logging = {
            'errors': [],
            'company_already_merged_with_target': 0,
            'company_already_merged': 0,
            'duns_already_assigned': 0,
        }

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        pk = parse_uuid(row['id'])
        company = Company.objects.get(pk=pk)
        duns_number = parse_limited_string(row['duns_number'], blank_value=None)

        if company.duns_number == duns_number:
            return

        if duns_number is not None and self.is_duns_already_assigned_to_another_company(
            company,
            duns_number,
        ):
            return

        company.duns_number = duns_number

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

    def is_duns_already_assigned_to_another_company(
        self,
        company: Company,
        duns_number: str,
    ) -> bool:
        """If another company exists with the target duns, this is an issue as duns numbers are
        unique. These are logged individually.

        :param company: The source company we want to update.
        :param duns_number: The duns number we want to give the source company.
        :return: Returns True if the duns number already exists for another company, False
            otherwise.
        """
        company_with_duns = Company.objects.filter(duns_number=duns_number).first()
        if not company_with_duns:
            return False

        if self.is_source_already_merged_into_target(company, company_with_duns):
            self.additional_logging['company_already_merged_with_target'] += 1
            return True

        if self.is_source_already_merged(company):
            self.additional_logging['company_already_merged'] += 1
            return True

        # If source is not merged but another company has the target duns, we cannot update
        # this company as duns numbers are unique on the Company model. Log this error.
        self.additional_logging['duns_already_assigned'] += 1
        self.additional_logging['errors'].append(
            {
                'id': company.pk,
                'duns_number': company_with_duns.duns_number,
                'error': (
                    'Cannot assign duns number to company as another company already has '
                    f'this duns number. Company with duns already: {company_with_duns.id}',
                ),
            },
        )
        return True

    def is_source_already_merged_into_target(
        self,
        company: Company,
        target_company: Company,
    ) -> bool:
        """Checks if the source has already been merged into another company with the target duns
        number. These companies should not have the duns number updated as they have been marked
        as a duplicate and merged into another company with that company having the correct duns
        number.

        :param company: The source company we want to update.
        :param target_company: A company which already has the target duns.
        :returns: True if the source company has already been merged into a company with the target
            duns numbers. False otherwise.
        """
        if company.transferred_to_id == target_company.id:
            return True
        return False

    def is_source_already_merged(self, company: Company) -> bool:
        """Checks if the source has already been merged into another company. These companies should
        not have the duns number updated as they have been marked as a duplicate and merged into
        another company.

        :param company: The source company we want to update.
        :returns: True if the source company has already been merged into a company. False
            otherwise.
        """
        if company.transferred_to_id:
            return True
        return False

    def handle(self, *args, **options):
        """Process the CSV file and logs some additional logging to help with the company duns update."""
        super().handle(*args, **options)
        logger.info('Errors:')
        logger.info(f'{self.additional_logging["errors"]}')
        logger.info(
            'Total companies where duns cannot be assigned as duns assigned to another company: '
            f'{self.additional_logging["duns_already_assigned"]}',
        )
        logger.info(
            'Total companies already merged with company matching target duns so not updated: '
            f'{self.additional_logging["company_already_merged_with_target"]}',
        )
        logger.info(
            'Total companies already merged and marked as duplicates so not updated: '
            f'{self.additional_logging["company_already_merged"]}',
        )
        self.additional_logging.clear()
