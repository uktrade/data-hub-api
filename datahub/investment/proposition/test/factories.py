import uuid

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.investment.proposition.constants import PropositionStatus
from datahub.investment.proposition.models import Proposition
from datahub.investment.test.factories import InvestmentProjectFactory


class PropositionFactory(factory.django.DjangoModelFactory):
    """Investment project proposition factory."""

    id = factory.LazyFunction(uuid.uuid4)

    investment_project = factory.SubFactory(InvestmentProjectFactory)
    adviser = factory.SubFactory(AdviserFactory)

    deadline = factory.Faker('future_date')
    status = PropositionStatus.ongoing

    name = factory.Sequence(lambda n: f'name {n}')
    scope = factory.Sequence(lambda n: f'scope {n}')

    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = Proposition
