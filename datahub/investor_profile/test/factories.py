import factory

from datahub.company.test.factories import CompanyFactory
from datahub.core.test.factories import to_many_field
from datahub.investor_profile.constants import ProfileType as ProfileTypeConstant


class InvestorProfileFactory(factory.django.DjangoModelFactory):
    """Investor profile factory."""

    investor_company = factory.SubFactory(CompanyFactory)
    profile_type_id = ProfileTypeConstant.large.value.id

    @to_many_field
    def client_contacts(self):
        """Add support for setting client_contacts."""
        return []

    class Meta:
        model = 'investor_profile.InvestorProfile'
