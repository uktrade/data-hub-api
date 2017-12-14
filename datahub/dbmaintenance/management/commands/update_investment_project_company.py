import uuid

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

    def _parse_company_id(self, company_id):
        """
        :param company_id: string representing uuid of the company
        :return: instance of UUID or None otherwise
        """
        if not company_id or company_id.lower().strip() == 'null':
            return None
        return uuid.UUID(company_id)

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

    def _can_update(self, company_ids):
        """Check if given list of company_ids exists.

        :param: company_ids: list of company ids
        :return: True if can update, otherwise False
        """
        return (
            Company.objects.values_list('id').filter(id__in=company_ids).count() ==
            len(company_ids)
        )

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
        investor_company_id = self._parse_company_id(row['investor_company_id'])
        intermediate_company_id = self._parse_company_id(row['intermediate_company_id'])
        uk_company_id = self._parse_company_id(row['uk_company_id'])
        uk_company_decided = self.get_uk_company_decided(row['uk_company_decided'])

        company_ids = [
            company_id for company_id in
            [investor_company_id, intermediate_company_id, uk_company_id]
            if company_id is not None
        ]
        if not self._can_update(company_ids):
            raise ValueError('Companies not found.')

        if self._should_update(
            investment_project,
            investor_company_id,
            intermediate_company_id,
            uk_company_id,
            uk_company_decided,
        ):
            investment_project.investor_company_id = investor_company_id
            investment_project.intermediate_company_id = intermediate_company_id
            investment_project.uk_company_id = uk_company_id
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
