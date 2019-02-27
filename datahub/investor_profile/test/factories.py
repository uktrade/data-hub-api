import factory

from datahub.company.test.factories import CompanyFactory
from datahub.investor_profile.constants import ProfileType as ProfileTypeConstant


class InvestorProfileFactory(factory.django.DjangoModelFactory):
    """Investor profile factory."""

    investor_company = factory.SubFactory(CompanyFactory)
    profile_type_id = ProfileTypeConstant.large.value.id

    class Meta:
        model = 'investor_profile.InvestorProfile'
