import uuid

import factory
from django.utils.timezone import now

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.omis.quote.models import TermsAndConditions


class QuoteFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    reference = factory.Faker('text', max_nb_chars=10)
    content = factory.Faker('text')
    expires_on = factory.Faker('future_date')
    terms_and_conditions = factory.LazyFunction(TermsAndConditions.objects.first)

    class Meta:
        model = 'omis-quote.Quote'


class CancelledQuoteFactory(QuoteFactory):
    """Cancelled Order factory."""

    cancelled_on = now()
    cancelled_by = factory.SelfAttribute('created_by')


class AcceptedQuoteFactory(QuoteFactory):
    """Accepted Order factory."""

    accepted_on = now()
    accepted_by = factory.SubFactory(ContactFactory)
