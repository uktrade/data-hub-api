from random import choice
from uuid import uuid4

import factory

from datahub.core.test.factories import to_many_field
from datahub.core.test.support.models import Book


class MetadataModelFactory(factory.django.DjangoModelFactory):
    """MetadataModel factory."""

    id = factory.LazyFunction(uuid4)
    name = factory.Faker('sentence')

    class Meta:
        model = 'support.MetadataModel'


class PersonFactory(factory.django.DjangoModelFactory):
    """Person factory."""

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

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
