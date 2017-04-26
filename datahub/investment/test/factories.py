import uuid
from datetime import date

import factory
from django.utils.timezone import now

from datahub.core import constants


class InvestmentProjectFactory(factory.django.DjangoModelFactory):
    """Company factory."""

    id = factory.Sequence(lambda x: '{0}'.format(uuid.uuid4()))
    name = factory.Sequence(lambda x: 'name {0}'.format(x))
    description = factory.Sequence(lambda x: 'desc {0}'.format(x))
    nda_signed = False
    estimated_land_date = date(2020, 1, 1)

    investment_type_id = constants.InvestmentType.fdi.value.id
    phase_id = constants.InvestmentProjectPhase.assign_pm.value.id
    sector_id = constants.Sector.aerospace_assembly_aircraft.value.id
    created_on = now()

    class Meta:
        model = 'investment.InvestmentProject'
