"""Model instance factories for investment tests."""

import uuid
from datetime import date
from decimal import Decimal

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import (
    InvestmentBusinessActivity,
    InvestmentProjectStage,
    InvestmentStrategicDriver,
    InvestmentType,
    ReferralSourceActivity,
    SalaryRange,
    Sector,
)
from datahub.core.test.factories import to_many_field
from datahub.core.test_utils import random_obj_for_model
from datahub.investment.project.constants import (
    FDISICGrouping,
    InvestmentActivityType,
    InvestorType,
    Involvement,
    LikelihoodToLand,
    SpecificProgramme,
)
from datahub.investment.project.models import InvestmentDeliveryPartner, InvestmentProject
from datahub.metadata.models import UKRegion


class InvestmentProjectFactory(factory.django.DjangoModelFactory):
    """Investment project factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    name = factory.Sequence(lambda n: f'name {n}')
    description = factory.Sequence(lambda n: f'desc {n}')
    comments = factory.Faker('text')
    estimated_land_date = date(2020, 1, 1)
    investment_type_id = InvestmentType.commitment_to_invest.value.id
    referral_source_activity_id = ReferralSourceActivity.cold_call.value.id
    investor_type_id = InvestorType.new_investor.value.id
    level_of_involvement_id = Involvement.no_involvement.value.id
    specific_programme_id = SpecificProgramme.space.value.id
    stage_id = InvestmentProjectStage.prospect.value.id
    sector_id = Sector.aerospace_assembly_aircraft.value.id
    investor_company = factory.SubFactory(CompanyFactory)
    client_relationship_manager = factory.SubFactory(AdviserFactory)
    referral_source_adviser = factory.SubFactory(AdviserFactory)
    likelihood_to_land_id = LikelihoodToLand.high.value.id
    archived_documents_url_path = factory.Faker('uri_path')
    created_on = now()

    @to_many_field
    def business_activities(self):
        """Add support for setting business_activities."""
        return [InvestmentBusinessActivity.retail.value.id]

    @to_many_field
    def client_contacts(self):
        """Add support for setting client_contacts."""
        return [ContactFactory().pk, ContactFactory().pk]

    @to_many_field
    def competitor_countries(self):
        """Add support for setting competitor_countries."""

    @to_many_field
    def strategic_drivers(self):
        """Add support for setting strategic_drivers."""

    @to_many_field
    def uk_region_locations(self):
        """Add support for setting uk_region_locations."""

    @to_many_field
    def actual_uk_regions(self):
        """Add support for setting actual_uk_regions."""

    @to_many_field
    def delivery_partners(self):
        """Add support for setting delivery_partners."""

    class Meta:
        model = 'investment.InvestmentProject'


class FDIInvestmentProjectFactory(InvestmentProjectFactory):
    """FDI Investment project factory."""

    investment_type_id = InvestmentType.fdi.value.id


class AssignPMInvestmentProjectFactory(InvestmentProjectFactory):
    """Investment project in the Assign PM stage."""

    stage_id = InvestmentProjectStage.assign_pm.value.id
    client_cannot_provide_total_investment = False
    total_investment = Decimal('100.0')
    number_new_jobs = 0
    client_considering_other_countries = False
    client_requirements = factory.Faker('text')
    site_decided = False

    @to_many_field
    def strategic_drivers(self):
        """Add support for setting strategic_drivers."""
        return [InvestmentStrategicDriver.access_to_market.value.id]

    @to_many_field
    def uk_region_locations(self):
        """Add support for setting uk_region_locations."""
        return [random_obj_for_model(UKRegion)]


class ActiveInvestmentProjectFactory(AssignPMInvestmentProjectFactory):
    """Investment project in the Active stage."""

    stage_id = InvestmentProjectStage.active.value.id
    project_assurance_adviser = factory.SubFactory(AdviserFactory)
    project_manager = factory.SubFactory(AdviserFactory)


class VerifyWinInvestmentProjectFactory(ActiveInvestmentProjectFactory):
    """Investment project in the Verify win stage."""

    stage_id = InvestmentProjectStage.verify_win.value.id
    client_cannot_provide_foreign_investment = False
    foreign_equity_investment = Decimal('100.0')
    government_assistance = False
    number_safeguarded_jobs = 0
    r_and_d_budget = True
    non_fdi_r_and_d_budget = False
    new_tech_to_uk = True
    export_revenue = True
    address_1 = factory.Faker('street_address')
    address_town = factory.Faker('city')
    address_postcode = factory.Faker('postcode')
    average_salary_id = SalaryRange.below_25000.value.id

    @to_many_field
    def actual_uk_regions(self):
        """Set a default value for actual_uk_regions."""
        return [random_obj_for_model(UKRegion)]

    @to_many_field
    def delivery_partners(self):
        """Sets default delivery partners."""
        return [random_obj_for_model(InvestmentDeliveryPartner)]


class WonInvestmentProjectFactory(VerifyWinInvestmentProjectFactory):
    """Investment project in the Won stage."""

    stage_id = InvestmentProjectStage.won.value.id
    status = InvestmentProject.STATUSES.won
    actual_land_date = factory.Faker('past_date')


class InvestmentProjectTeamMemberFactory(factory.django.DjangoModelFactory):
    """Investment project team member factory."""

    investment_project = factory.SubFactory(InvestmentProjectFactory)
    adviser = factory.SubFactory(AdviserFactory)
    role = factory.Sequence(lambda n: f'role {n}')

    class Meta:
        model = 'investment.InvestmentProjectTeamMember'


class InvestmentActivityFactory(factory.django.DjangoModelFactory):
    """Investment activity factory."""

    investment_project = factory.SubFactory(InvestmentProjectFactory)

    text = factory.Faker('name')
    activity_type_id = InvestmentActivityType.change.value.id

    class Meta:
        model = 'investment.InvestmentActivity'


class GVAMultiplierFactory(factory.django.DjangoModelFactory):
    """GVA Multiplier factory."""

    fdi_sic_grouping_id = FDISICGrouping.retail.value.id
    financial_year = 2019
    multiplier = Decimal('0.1250')

    class Meta:
        model = 'investment.GVAMultiplier'
