import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory
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

    class Meta:
        model = 'company_list.PipelineItem'
