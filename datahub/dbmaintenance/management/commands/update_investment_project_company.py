from functools import lru_cache

from datahub.company.models import Company
from datahub.investment.models import InvestmentProject
from ..base import CSVBaseCommand


class Command(CSVBaseCommand):
    """Command to update investment_project.

    investor_company, intermediate_company, uk_company, uk_company_decided.
    """

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--simulate',
            action='store_true',
            dest='simulate',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )

    @lru_cache(maxsize=None)
    def get_company(self, company_id):
        """
        :param company_id: uuid of the company
        :return: instance of Company with id == company_id if it exists,
            None otherwise
        """
        if not company_id or company_id.lower().strip() == 'null':
            return None
        return Company.objects.get(id=company_id)

    def _should_update(self,
                       investment_project,
                       investor_company,
                       intermediate_company,
                       uk_company,
                       uk_company_decided):
        """
        Checks if Investment project should be updated.

        :param investment_project: instance of InvestmentProject
        :param investor_company: instance of Company or None
        :param intermediate_company: instance of Company or None
        :param uk_company: instance of Company or None
        :param uk_company_decided: Boolean
        :return: True if investment project needs to be updated
        """
        return (investment_project.investor_company != investor_company or
                investment_project.intermediate_company != intermediate_company or
                investment_project.uk_company != uk_company or
                investment_project.uk_company_decided != uk_company_decided)

    def get_uk_company_decided(self, uk_company_decided):
        """
        :param uk_company_decided: string containing either '1' or '0'
        :return: Boolean
        """
        translate = {
            '0': False,
            '1': True,
        }
        return translate[uk_company_decided.strip()]

    def _process_row(self, row, simulate=False, **options):
        """Process one single row."""
        investment_project = InvestmentProject.objects.get(pk=row['id'])
        investor_company = self.get_company(row['investor_company_id'])
        intermediate_company = self.get_company(row['intermediate_company_id'])
        uk_company = self.get_company(row['uk_company_id'])
        uk_company_decided = self.get_uk_company_decided(row['uk_company_decided'])

        if self._should_update(
            investment_project,
            investor_company,
            intermediate_company,
            uk_company,
            uk_company_decided,
        ):
            investment_project.investor_company = investor_company
            investment_project.intermediate_company = intermediate_company
            investment_project.uk_company = uk_company
            investment_project.uk_company_decided = uk_company_decided
            if not simulate:
                investment_project.save(
                    update_fields=(
                        'investor_company',
                        'intermediate_company',
                        'uk_company',
                        'uk_company_decided',
                    )
                )
