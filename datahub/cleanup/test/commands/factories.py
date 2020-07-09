from datahub.core.test.factories import to_many_field
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.user.company_list.test.factories import PipelineItemFactory


class ShallowInvestmentProjectFactory(InvestmentProjectFactory):
    """
    Same as InvestmentProjectFactory but with reduced dependencies
    so that we can test specific references without extra noise.
    """

    intermediate_company = None
    investor_company = None
    uk_company = None

    @to_many_field
    def client_contacts(self):
        """No client contacts."""
        return []
