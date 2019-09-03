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


class LegacyCompanyListItemFactory(CompanyListItemFactory):
    """
    Factory for an item on a user's legacy company list.

    TODO: This should be removed once the legacy company list views have been removed.
    """

    list = factory.SubFactory(
        CompanyListFactory,
        adviser=factory.SubFactory(AdviserFactory),
        is_legacy_default=True,
    )
