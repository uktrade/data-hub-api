import factory

from datahub.company.test.factories import CompanyFactory
from datahub.investment.investor_profile.constants import ProfileType as ProfileTypeConstant


class LargeInvestorProfileFactory(factory.django.DjangoModelFactory):
    """Large Capital Investor profile factory."""

    investor_company = factory.SubFactory(CompanyFactory)
    profile_type_id = ProfileTypeConstant.large.value.id

    class Meta:
        model = 'investor_profile.InvestorProfile'


class GrowthInvestorProfileFactory(LargeInvestorProfileFactory):
    """Growth Capital Investor profile factory."""

    profile_type_id = ProfileTypeConstant.growth.value.id
