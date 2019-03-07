from datahub.core.test.factories import to_many_field
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory


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


class CompanyInteractionFactoryWithoutContacts(CompanyInteractionFactory):
    """
    Same as CompanyInteractionFactory but with reduced dependencies
    so that we can test specific references without extra noise.

    TODO: Remove once Interaction.contact has been removed.
    """

    contact = None

    @to_many_field
    def contacts(self):
        """Default to no contacts."""
        return []
