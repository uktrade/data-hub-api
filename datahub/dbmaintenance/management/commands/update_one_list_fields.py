from functools import lru_cache
from logging import getLogger

import reversion
from django.db.models import Q

from datahub.company.models import Advisor, Company
from datahub.dbmaintenance.management.base import CSVBaseCommand
from datahub.dbmaintenance.utils import parse_uuid
from datahub.metadata.models import CompanyClassification


logger = getLogger(__name__)


class Command(CSVBaseCommand):
    """
    Command to update:
    - Company.classification
    - Company.one_list_account_owner

    If --reset-unmatched=true, all the records not in the CSV will have
    the fields above set to None.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--reset-unmatched',
            action='store_true',
            default=False,
            help=(
                'If true, Data Hub records not present '
                'in the CSV will have classification and one_list_account_owner set to None.'
            ),
        )

    def _handle(self, *args, simulate=False, reset_unmatched=False, **options):
        """
        Same as the super class but it adds some logic before and after it.

        This is because we want to reset all the records that are not found in the CSV if
        reset-unmatched is speficied.
        """
        # if reset_unmatched, store current state in a dict so that we can remove the companies
        # as we process them and reset the remaining items.
        if reset_unmatched:
            qs = Company.objects.filter(
                Q(classification_id__isnull=False) | Q(one_list_account_owner_id__isnull=False),
            )
            self.companies_to_reset = {company.id: company for company in qs}
        else:
            self.companies_to_reset = {}

        # process CSV and remove companies from self.companies_to_reset
        result = super()._handle(
            *args,
            reset_unmatched=reset_unmatched,
            simulate=simulate,
            **options,
        )

        # reset all remaining unmatched companies
        if reset_unmatched:
            for company in self.companies_to_reset.values():
                succeeded = self.reset_unmatched(company, simulate)
                result[succeeded] += 1

        return result

    def reset_unmatched(self, company, simulate):
        """
        Reset one list fields for `company`.

        :param company: the Company to update
        :param simulate: True if the change should not be committed to the database
        :returns: True if the company has been processed successfully, False otherwise.
        """
        try:
            self._update_company(
                company,
                new_classification_id=None,
                new_one_list_account_owner_id=None,
                simulate=simulate,
            )
        except Exception as e:
            logger.exception(f'Resetting company {company} - Failed')
            return False
        else:
            logger.info(f'Resetting company {company} - OK')
            return True

    @lru_cache(maxsize=None)
    def get_classification(self, pk):
        """
        :param pk: primary key of the instance to get
        :returns: CompanyClassification with id == `pk`
        """
        if not pk:
            return None
        return CompanyClassification.objects.get(pk=pk)

    @lru_cache(maxsize=None)
    def get_adviser(self, pk):
        """
        :param pk: primary key of the instance to get
        :returns: Advisor with id == `pk`
        """
        if not pk:
            return None
        return Advisor.objects.get(pk=pk)

    def _update_company(
        self, company, new_classification_id, new_one_list_account_owner_id, simulate,
    ):
        """
        Update `company` with the new values.

        :param new_classification_id: new CompanyClassification value
        :param new_one_list_account_owner_id: new Advisor value
        :param simulate: True if the change should not be committed to the database
        """
        company.classification = self.get_classification(new_classification_id)
        company.one_list_account_owner = self.get_adviser(new_one_list_account_owner_id)

        if simulate:
            return

        with reversion.create_revision():
            company.save(
                update_fields=(
                    'classification_id',
                    'one_list_account_owner_id',
                ),
            )
            reversion.set_comment('Classification and One List account owner correction.')

    def _should_update(self, company, classification_id, one_list_account_owner_id):
        """
        Check if `company` should be updated.

        :param company: Company to update
        :param classification_id: new CompanyClassification value
        :param one_list_account_owner_id: new Advisor value
        :return: True if `company` needs updating
        """
        return (
            company.classification_id != classification_id
        ) or (
            company.one_list_account_owner_id != one_list_account_owner_id
        )

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        company = Company.objects.get(pk=parse_uuid(row['id']))

        # remove company.pk from the list of companies to reset
        self.companies_to_reset.pop(company.pk, None)

        classification_id = parse_uuid(row['classification_id'])
        one_list_account_owner_id = parse_uuid(row['one_list_account_owner_id'])

        if self._should_update(company, classification_id, one_list_account_owner_id):
            self._update_company(company, classification_id, one_list_account_owner_id, simulate)
