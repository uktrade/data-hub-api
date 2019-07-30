from random import choice
from uuid import uuid4

import factory

from datahub.core import constants
from datahub.core.test.factories import to_many_field
from datahub.core.test.support.models import Book


class MetadataModelFactory(factory.django.DjangoModelFactory):
    """MetadataModel factory."""

    id = factory.LazyFunction(uuid4)
    name = factory.Faker('sentence')

    class Meta:
        model = 'support.MetadataModel'


class ForeignAndM2MModelFactory(factory.django.DjangoModelFactory):
    """ForeignAndM2MModel factory."""

    value = factory.SubFactory(MetadataModelFactory)

    @to_many_field
    def values(self):
        """Post-generation hook for values."""
        return [self.value] if self.value else []

    class Meta:
        model = 'support.ForeignAndM2MModel'


class PersonFactory(factory.django.DjangoModelFactory):
    """Person factory."""

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    country = factory.Faker('country')

    class Meta:
        model = 'support.Person'


class BookFactory(factory.django.DjangoModelFactory):
    """Book factory."""

    name = factory.Faker('sentence')
    published_on = factory.Faker('date_object')
    proofreader = factory.SubFactory(PersonFactory)
    genre = factory.LazyFunction(lambda: choice(Book.GENRES)[0])

    @to_many_field
    def authors(self):
        """Post-generation hook for authors."""
        return [PersonFactory()]

    class Meta:
        model = 'support.Book'


class PersonListItemFactory(factory.django.DjangoModelFactory):
    """PersonListItem factory."""

    person = factory.SubFactory(PersonFactory)

    class Meta:
        model = 'support.PersonListItem'


class MultiAddressModelFactory(factory.django.DjangoModelFactory):
    """MultiAddressModel factory."""

    primary_address_1 = factory.Sequence(lambda n: f'Apt {n}.')
    primary_address_2 = factory.Sequence(lambda n: f'{n} Foo st.')
    primary_address_country_id = constants.Country.united_kingdom.value.id
    primary_address_county = factory.Faker('text')
    primary_address_postcode = factory.Faker('postcode')
    primary_address_town = factory.Faker('city')

    secondary_address_1 = factory.Sequence(lambda n: f'Apt {n}.')
    secondary_address_2 = factory.Sequence(lambda n: f'{n} Foo st.')
    secondary_address_country_id = constants.Country.united_kingdom.value.id
    secondary_address_county = factory.Faker('text')
    secondary_address_postcode = factory.Faker('postcode')
    secondary_address_town = factory.Faker('city')

    class Meta:
        model = 'support.MultiAddressModel'
