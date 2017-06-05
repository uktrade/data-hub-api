"""Model instance factories for investment tests."""

import uuid
from datetime import date

import factory
from django.utils.timezone import now

from datahub.core.constants import (
    InvestmentType, ReferralSourceActivity, InvestmentProjectPhase, Sector,
    InvestmentBusinessActivity, FDIType
)
from datahub.company.test.factories import (
    AdvisorFactory, CompanyFactory
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

    phase_id = InvestmentProjectPhase.prospect.value.id
    sector_id = Sector.aerospace_assembly_aircraft.value.id
    investor_company = factory.SubFactory(CompanyFactory)
    client_relationship_manager = factory.SubFactory(AdvisorFactory)
    referral_source_adviser = factory.SubFactory(AdvisorFactory)
    project_shareable = False
    business_activities = [InvestmentBusinessActivity.retail.value.id]
    created_on = now()

    class Meta:
        model = 'investment.InvestmentProject'
