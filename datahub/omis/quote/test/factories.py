import uuid
import factory

from datahub.company.test.factories import AdviserFactory


class QuoteFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    reference = factory.Faker('text', max_nb_chars=10)
    content = factory.Faker('text')

    class Meta:  # noqa: D101
        model = 'omis-quote.Quote'
