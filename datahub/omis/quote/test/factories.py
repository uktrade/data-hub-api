import uuid
import factory

from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory


class QuoteFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    reference = factory.Faker('text', max_nb_chars=10)
    content = factory.Faker('text')
    expires_on = factory.Faker('future_date')

    class Meta:  # noqa: D101
        model = 'omis-quote.Quote'


class CancelledQuoteFactory(QuoteFactory):
    """Cancelled Order factory."""

    cancelled_on = now()
    cancelled_by = factory.SubFactory(AdviserFactory)
