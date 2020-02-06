import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory
from datahub.investment.project.proposition.constants import PropositionStatus
from datahub.investment.project.proposition.models import Proposition
from datahub.investment.project.test.factories import InvestmentProjectFactory


class PropositionFactory(factory.django.DjangoModelFactory):
    """Investment project proposition factory."""

    investment_project = factory.SubFactory(InvestmentProjectFactory)
    adviser = factory.SubFactory(AdviserFactory)

    deadline = factory.Faker('future_date')
    status = PropositionStatus.ONGOING

    name = factory.Faker('text')
    scope = factory.Faker('text')

    created_on = now()
    created_by = factory.SelfAttribute('adviser')
    modified_by = factory.SelfAttribute('adviser')

    class Meta:
        model = Proposition
