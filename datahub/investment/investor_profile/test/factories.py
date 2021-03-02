from datetime import date

import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.constants import (
    Country as CountryConstant,
    UKRegion as UKRegionConstant,
)
from datahub.core.test.factories import to_many_field
from datahub.investment.investor_profile.constants import (
    RequiredChecksConducted as RequiredChecksConductedConstant,
)
from datahub.investment.investor_profile.test.constants import (
    AssetClassInterest as AssetClassInterestConstant,
    ConstructionRisk as ConstructionRiskConstant,
    DealTicketSize as DealTicketSizeConstant,
    DesiredDealRole as DesiredDealRoleConstant,
    EquityPercentage as EquityPercentageConstant,
    InvestorType as InvestorTypeConstant,
    LargeCapitalInvestmentTypes as InvestmentTypesConstant,
    Restriction as RestrictionConstant,
    ReturnRate as ReturnRateConstant,
    TimeHorizon as TimeHorizonConstant,
)


class LargeCapitalInvestorProfileFactory(factory.django.DjangoModelFactory):
    """Large capital investor profile factory."""

    investor_company = factory.SubFactory(CompanyFactory)

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
        model = 'investor_profile.LargeCapitalInvestorProfile'


class CompleteLargeCapitalInvestorProfileFactory(LargeCapitalInvestorProfileFactory):
    """Complete Large Capital Investor profile factory."""

    investor_description = factory.Faker('text')
    investable_capital = 10000
    global_assets_under_management = 20000
    required_checks_conducted_id = RequiredChecksConductedConstant.issues_identified.value.id
    required_checks_conducted_by = factory.SubFactory(AdviserFactory)
    required_checks_conducted_on = date(2020, 1, 1)
    investor_type_id = InvestorTypeConstant.state_pension_fund.value.id
    minimum_return_rate_id = ReturnRateConstant.up_to_five_percent.value.id
    minimum_equity_percentage_id = EquityPercentageConstant.zero_percent.value.id
    notes_on_locations = factory.Faker('text')
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)

    @to_many_field
    def construction_risks(self):
        """Construction risks."""
        return [
            ConstructionRiskConstant.operational.value.id,
            ConstructionRiskConstant.greenfield.value.id,
        ]

    @to_many_field
    def deal_ticket_sizes(self):
        """Deal ticket sizes."""
        return [DealTicketSizeConstant.up_to_forty_nine_million.value.id]

    @to_many_field
    def asset_classes_of_interest(self):
        """Asset classes of interest."""
        return [
            AssetClassInterestConstant.biomass.value.id,
            AssetClassInterestConstant.biofuel.value.id,
        ]

    @to_many_field
    def investment_types(self):
        """Investment types."""
        return [
            InvestmentTypesConstant.direct_investment_in_project_equity.value.id,
        ]

    @to_many_field
    def time_horizons(self):
        """Time horizons."""
        return [
            TimeHorizonConstant.up_to_five_years.value.id,
            TimeHorizonConstant.five_to_nine_years.value.id,
        ]

    @to_many_field
    def restrictions(self):
        """Restrictions."""
        return [
            RestrictionConstant.inflation_adjustment.value.id,
            RestrictionConstant.liquidity.value.id,
        ]

    @to_many_field
    def desired_deal_roles(self):
        """Desired deal roles."""
        return [
            DesiredDealRoleConstant.lead_manager.value.id,
        ]

    @to_many_field
    def uk_region_locations(self):
        """UK region locations."""
        return [
            UKRegionConstant.north_west.value.id,
            UKRegionConstant.north_east.value.id,
        ]

    @to_many_field
    def other_countries_being_considered(self):
        """Other countries being considered."""
        return [
            CountryConstant.ireland.value.id,
            CountryConstant.canada.value.id,
        ]
