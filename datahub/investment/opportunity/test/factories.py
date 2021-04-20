from datetime import date

import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.constants import (
    UKRegion as UKRegionConstant,
)
from datahub.core.test.factories import to_many_field
from datahub.investment.investor_profile.constants import (
    RequiredChecksConducted as RequiredChecksConductedConstant,
)
from datahub.investment.investor_profile.test.constants import (
    AssetClassInterest as AssetClassInterestConstant,
    ConstructionRisk as ConstructionRiskConstant,
    LargeCapitalInvestmentTypes as InvestmentTypesConstant,
    ReturnRate as ReturnRateConstant,
    TimeHorizon as TimeHorizonConstant,
)
from datahub.investment.opportunity.test.constants import (
    AbandonmentReason as AbandonmentReasonConstant,
    OpportunityStatus as OpportunityStatusConstant,
    OpportunityType as OpportunityTypeConstant,
    OpportunityValueType as OpportunityValueTypeConstant,
    SourceOfFunding as SourceOfFundingConstant,
)
from datahub.investment.project.test.factories import InvestmentProjectFactory


class LargeCapitalOpportunityFactory(factory.django.DjangoModelFactory):
    """Large capital opportunity factory."""

    lead_dit_relationship_manager = factory.SubFactory(AdviserFactory)
    dit_support_provided = False
    status_id = OpportunityStatusConstant.abandoned.value.id
    type_id = OpportunityTypeConstant.large_capital.value.id

    @to_many_field
    def uk_region_locations(self):
        """UK region locations."""
        return []

    @to_many_field
    def promoters(self):
        """Promoters."""
        return []

    @to_many_field
    def other_dit_contacts(self):
        """Other DIT contacts."""
        return []

    @to_many_field
    def asset_classes(self):
        """Asset classes."""
        return []

    @to_many_field
    def construction_risks(self):
        """Construction risks."""
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
    def investment_projects(self):
        """Investment projects."""
        return []

    @to_many_field
    def reasons_for_abandonment(self):
        """Reasons for abandonment."""
        return []

    @to_many_field
    def sources_of_funding(self):
        """Sources of funding."""
        return []

    class Meta:
        model = 'opportunity.LargeCapitalOpportunity'


class CompleteLargeCapitalOpportunityFactory(LargeCapitalOpportunityFactory):
    """Complete Large Capital opportunity factory."""

    name = factory.Faker('sentence', nb_words=5)
    description = factory.Faker('text')

    @to_many_field
    def promoters(self):
        """Promoters."""
        return [CompanyFactory()]

    @to_many_field
    def uk_region_locations(self):
        """UK region locations."""
        return [
            UKRegionConstant.north_west.value.id,
            UKRegionConstant.north_east.value.id,
        ]

    dit_support_provided = False
    total_investment_sought = 10000
    current_investment_secured = 5000
    opportunity_value = 50000
    opportunity_value_type_id = OpportunityValueTypeConstant.capital_expenditure.value.id
    estimated_return_rate_id = ReturnRateConstant.up_to_five_percent.value.id
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)

    @to_many_field
    def asset_classes(self):
        """Asset classes."""
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

    required_checks_conducted_id = RequiredChecksConductedConstant.issues_identified.value.id
    required_checks_conducted_by = factory.SubFactory(AdviserFactory)
    required_checks_conducted_on = date(2020, 1, 1)

    @to_many_field
    def construction_risks(self):
        """Construction risks."""
        return [
            ConstructionRiskConstant.operational.value.id,
            ConstructionRiskConstant.greenfield.value.id,
        ]

    @to_many_field
    def investment_projects(self):
        """Investment projects."""
        return [InvestmentProjectFactory()]

    @to_many_field
    def time_horizons(self):
        """Time horizons."""
        return [
            TimeHorizonConstant.up_to_five_years.value.id,
            TimeHorizonConstant.five_to_nine_years.value.id,
        ]

    @to_many_field
    def sources_of_funding(self):
        """Sources of funding."""
        return [SourceOfFundingConstant.international.value.id]
    funding_supporting_details = factory.Faker('text')

    @to_many_field
    def reasons_for_abandonment(self):
        """Reasons for abandonment."""
        return [AbandonmentReasonConstant.promoter_abandoned_the_opportunity.value.id]

    why_abandoned = factory.Faker('text')
