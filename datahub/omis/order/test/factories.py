"""Model instance factories for order tests."""

import uuid

import factory

from datahub.company.test.factories import CompanyFactory, ContactFactory, AdviserFactory
from datahub.core.constants import Country


class OrderFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(ContactFactory)
    primary_market_id = Country.france.value.id

    class Meta:
        model = 'order.Order'


class OrderSubscriberFactory(factory.django.DjangoModelFactory):
    """Order Subscriber factory."""

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    order = factory.SubFactory(OrderFactory)
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'order.OrderSubscriber'
