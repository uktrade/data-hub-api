import uuid

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.investment.evidence.models import EvidenceGroup
from datahub.investment.test.factories import InvestmentProjectFactory


class EvidenceGroupFactory(factory.django.DjangoModelFactory):
    """Investment project evidence group factory."""

    id = factory.LazyFunction(uuid.uuid4)

    investment_project = factory.SubFactory(InvestmentProjectFactory)

    name = factory.Faker('text')

    created_on = now()
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)

    class Meta:
        model = EvidenceGroup
