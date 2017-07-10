"""Model instance factories for investment tests."""

import uuid
from datetime import date

import factory
from django.utils.timezone import now

from datahub.core.constants import (
    InvestmentType, ReferralSourceActivity, InvestmentProjectStage, Sector
)
from datahub.core.test.factories import to_many_field
from datahub.company.test.factories import (
    AdviserFactory, CompanyFactory
)


class InvestmentProjectFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    id = factory.Sequence(lambda _: str(uuid.uuid4()))
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
        pass

    @to_many_field
    def client_contacts(self):
        pass

    @to_many_field
    def competitor_countries(self):
        pass

    @to_many_field
    def strategic_drivers(self):
        pass

    @to_many_field
    def uk_region_locations(self):
        pass

    class Meta:
        model = 'investment.InvestmentProject'
