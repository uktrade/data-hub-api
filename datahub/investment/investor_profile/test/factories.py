import factory

from datahub.company.test.factories import CompanyFactory
from datahub.core.test.factories import to_many_field
from datahub.investment.investor_profile.constants import ProfileType as ProfileTypeConstant


class LargeInvestorProfileFactory(factory.django.DjangoModelFactory):
    """Large Capital Investor profile factory."""

    investor_company = factory.SubFactory(CompanyFactory)
    profile_type_id = ProfileTypeConstant.large.value.id

    @to_many_field
    def construction_risks(self):
        """Construction risks."""
        return []

    @to_many_field
    def deal_ticket_sizes(self):
        """Deal ticket sizes."""
        return []

    @to_many_field
    def asset_classes_of_interest(self):
        """Asset classes of interest."""
        return []

    @to_many_field
    def investment_types(self):
        """Investment types."""
        return []

    @to_many_field
    def time_horizons(self):
        """Time horizons."""
        return []

    @to_many_field
    def restrictions(self):
        """Restrictions."""
        return []

    @to_many_field
    def desired_deal_roles(self):
        """Desired deal roles."""
        return []

    @to_many_field
    def uk_region_locations(self):
        """UK region locations."""
        return []

    @to_many_field
    def other_countries_being_considered(self):
        """Other countries being considered."""
        return []

    class Meta:
        model = 'investor_profile.InvestorProfile'


class GrowthInvestorProfileFactory(LargeInvestorProfileFactory):
    """Growth Capital Investor profile factory."""

    profile_type_id = ProfileTypeConstant.growth.value.id
