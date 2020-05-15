import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.metadata.test.factories import SectorFactory
from datahub.user.company_list.models import PipelineItem


class CompanyListFactory(factory.django.DjangoModelFactory):
    """Factory for a user's company list."""

    name = factory.Faker('sentence')
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'company_list.CompanyList'


class CompanyListItemFactory(factory.django.DjangoModelFactory):
    """Factory for an item on a user's company list."""

    company = factory.SubFactory(CompanyFactory)
    list = factory.SubFactory(CompanyListFactory)

    class Meta:
        model = 'company_list.CompanyListItem'


class PipelineItemFactory(factory.django.DjangoModelFactory):
    """Factory for a pipeline item"""

    name = factory.Faker('name')
    company = factory.SubFactory(CompanyFactory)
    adviser = factory.SubFactory(AdviserFactory)
    status = PipelineItem.Status.LEADS
    contact = factory.SubFactory(ContactFactory, company=factory.SelfAttribute('..company'))
    sector = factory.SubFactory(SectorFactory)
    potential_value = 1000000
    likelihood_to_win = PipelineItem.LikelihoodToWin.MEDIUM
    expected_win_date = factory.Faker('future_date', end_date='+3y')

    class Meta:
        model = 'company_list.PipelineItem'
