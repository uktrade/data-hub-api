"""Model instance factories for order tests."""

import uuid

import factory

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Country, Sector


class OrderFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    id = factory.LazyFunction(lambda: uuid.uuid4())
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    company = factory.SubFactory(CompanyFactory)
    contact = factory.LazyAttribute(lambda o: ContactFactory(company=o.company))
    primary_market_id = Country.france.value.id
    sector_id = Sector.aerospace_assembly_aircraft.value.id

    class Meta:  # noqa: D101
        model = 'order.Order'


class OrderSubscriberFactory(factory.django.DjangoModelFactory):
    """Order Subscriber factory."""

    id = factory.LazyFunction(lambda: uuid.uuid4())
    order = factory.SubFactory(OrderFactory)
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:  # noqa: D101
        model = 'order.OrderSubscriber'


class OrderAssigneeFactory(factory.django.DjangoModelFactory):
    """Order Assignee factory."""

    id = factory.LazyFunction(lambda: uuid.uuid4())
    order = factory.SubFactory(OrderFactory)
    adviser = factory.SubFactory(AdviserFactory)
    estimated_time = 120

    class Meta:  # noqa: D101
        model = 'order.OrderAssignee'
