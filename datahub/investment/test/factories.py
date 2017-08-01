"""Model instance factories for investment tests."""

import uuid
from datetime import date

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core.constants import (
    InvestmentProjectStage, InvestmentType, ReferralSourceActivity, Sector
)
from datahub.core.test.factories import to_many_field


class InvestmentProjectFactory(factory.django.DjangoModelFactory):
    """Investment project factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    name = factory.Sequence(lambda n: f'name {n}')
    description = factory.Sequence(lambda n: f'desc {n}')
    nda_signed = False
    estimated_land_date = date(2020, 1, 1)
    investment_type_id = InvestmentType.commitment_to_invest.value.id
    referral_source_activity_id = ReferralSourceActivity.cold_call.value.id

    stage_id = InvestmentProjectStage.prospect.value.id
    sector_id = Sector.aerospace_assembly_aircraft.value.id
    investor_company = factory.SubFactory(CompanyFactory)
    client_relationship_manager = factory.SubFactory(AdviserFactory)
    referral_source_adviser = factory.SubFactory(AdviserFactory)
    project_shareable = False
    likelihood_of_landing = 90
    created_on = now()

    @to_many_field
    def business_activities(self):
        """Add support for setting business_activities."""

    @to_many_field
    def client_contacts(self):
        """Add support for setting client_contacts."""

    @to_many_field
    def competitor_countries(self):
        """Add support for setting competitor_countries."""

    @to_many_field
    def strategic_drivers(self):
        """Add support for setting strategic_drivers."""

    @to_many_field
    def uk_region_locations(self):
        """Add support for setting uk_region_locations."""

    class Meta:  # noqa: D101
        model = 'investment.InvestmentProject'


class InvestmentProjectTeamMemberFactory(factory.django.DjangoModelFactory):
    """Investment project team member factory."""

    investment_project = factory.SubFactory(InvestmentProjectFactory)
    adviser = factory.SubFactory(AdviserFactory)
    role = factory.Sequence(lambda n: f'role {n}')

    class Meta:  # noqa: D101
        model = 'investment.InvestmentProjectTeamMember'
