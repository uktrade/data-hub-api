import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory


class CompanyListFactory(factory.django.DjangoModelFactory):
    """Factory for a user's company list."""

    name = factory.Faker('sentence')
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'company_list.CompanyList'


class CompanyListItemFactory(factory.django.DjangoModelFactory):
    """Factory for an item on a user's company list."""

    adviser = factory.SelfAttribute('list.adviser')
    company = factory.SubFactory(CompanyFactory)
    list = factory.SubFactory(CompanyListFactory)

    class Meta:
        model = 'company_list.CompanyListItem'
