import uuid
import factory


class QuoteFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    id = factory.LazyFunction(uuid.uuid4)
    reference = factory.Faker('text', max_nb_chars=10)
    content = factory.Faker('text')

    class Meta:  # noqa: D101
        model = 'omis-quote.Quote'
