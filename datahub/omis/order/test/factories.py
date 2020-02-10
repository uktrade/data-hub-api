import datetime

import factory
from django.utils.timezone import now, utc

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Country, Sector, UKRegion
from datahub.core.test.factories import to_many_field
from datahub.omis.invoice.models import Invoice
from datahub.omis.order.constants import OrderStatus, VATStatus
from datahub.omis.order.models import CancellationReason, ServiceType
from datahub.omis.quote.test.factories import (
    AcceptedQuoteFactory,
    CancelledQuoteFactory,
    QuoteFactory,
)


class OrderFactory(factory.django.DjangoModelFactory):
    """Order factory."""

    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SelfAttribute('created_by')
    company = factory.SubFactory(CompanyFactory)
    contact = factory.SubFactory(
        ContactFactory,
        company=factory.SelfAttribute('..company'),
    )
    primary_market_id = Country.france.value.id
    sector_id = Sector.aerospace_assembly_aircraft.value.id
    uk_region_id = UKRegion.england.value.id
    description = factory.Faker('text')
    contacts_not_to_approach = factory.Faker('text')
    product_info = factory.Faker('text')
    further_info = factory.Faker('text')
    existing_agents = factory.Faker('text')
    permission_to_approach_contacts = factory.Faker('text')
    delivery_date = factory.LazyFunction(
        lambda: (now() + datetime.timedelta(days=60)).date(),
    )
    contact_email = factory.Faker('email')
    contact_phone = '+44 (0)7123 123456'
    status = OrderStatus.draft
    po_number = factory.Faker('text', max_nb_chars=50)
    discount_value = factory.Faker('random_int', max=100)
    discount_label = factory.Faker('text', max_nb_chars=50)
    vat_status = VATStatus.EU
    vat_number = '0123456789'
    vat_verified = True
    billing_company_name = factory.LazyAttribute(lambda o: o.company.name)
    billing_contact_name = factory.Faker('name')
    billing_email = factory.Faker('email')
    billing_phone = '+44 (0)444 123456'
    billing_address_1 = factory.Sequence(lambda n: f'Apt {n}.')
    billing_address_2 = factory.Sequence(lambda n: f'{n} Foo st.')
    billing_address_country_id = Country.united_kingdom.value.id
    billing_address_county = factory.Faker('text')
    billing_address_postcode = factory.Faker('postcode')
    billing_address_town = factory.Faker('city')

    @to_many_field
    def service_types(self):
        """
        Add support for setting service_types.
        If nothing specified when instantiating the object, the value returned by
        this method will be used by default.
        """
        return ServiceType.objects.filter(disabled_on__isnull=True).order_by('?')[:2]

    @to_many_field
    def assignees(self):
        """
        Add support for setting assignees.
        If nothing specified when instantiating the object, the value returned by
        this method will be used by default.
        """
        return OrderAssigneeFactory.create_batch(1, order=self, is_lead=True)

    class Meta:
        model = 'order.Order'


class OrderWithOpenQuoteFactory(OrderFactory):
    """Order factory with an active quote."""

    quote = factory.SubFactory(QuoteFactory)
    status = OrderStatus.quote_awaiting_acceptance


class OrderWithCancelledQuoteFactory(OrderFactory):
    """Order factory with a cancelled quote."""

    quote = factory.SubFactory(CancelledQuoteFactory)


class OrderWithAcceptedQuoteFactory(OrderFactory):
    """Order factory with an accepted quote."""

    quote = factory.SubFactory(AcceptedQuoteFactory)
    status = OrderStatus.quote_accepted

    @factory.post_generation
    def set_invoice(self, create, extracted, **kwargs):
        """Set invoice after creating the instance."""
        if not create:
            return
        self.invoice = Invoice.objects.create_from_order(self)


class OrderCompleteFactory(OrderWithAcceptedQuoteFactory):
    """Factory for orders marked as paid."""

    status = OrderStatus.complete
    completed_on = factory.Faker('date_time', tzinfo=utc)
    completed_by = factory.SubFactory(AdviserFactory)


class OrderCancelledFactory(OrderWithAcceptedQuoteFactory):
    """Factory for cancelled orders."""

    status = OrderStatus.cancelled
    cancelled_on = factory.Faker('date_time', tzinfo=utc)
    cancelled_by = factory.SubFactory(AdviserFactory)
    cancellation_reason = factory.LazyFunction(CancellationReason.objects.first)


class OrderPaidFactory(OrderWithAcceptedQuoteFactory):
    """Factory for orders marked as paid."""

    paid_on = factory.Faker('date_time', tzinfo=utc)
    status = OrderStatus.paid


class OrderWithoutAssigneesFactory(OrderFactory):
    """Order factory without assignees."""

    @to_many_field
    def assignees(self):
        """No assignees for this order."""
        return []


class OrderWithoutLeadAssigneeFactory(OrderFactory):
    """Order factory without assignees."""

    @to_many_field
    def assignees(self):
        """Create non-lead assignees."""
        return OrderAssigneeFactory.create_batch(2, order=self, is_lead=False)


class OrderSubscriberFactory(factory.django.DjangoModelFactory):
    """Order Subscriber factory."""

    created_by = factory.SubFactory(AdviserFactory)
    order = factory.SubFactory(OrderFactory)
    adviser = factory.SubFactory(AdviserFactory)

    class Meta:
        model = 'order.OrderSubscriber'


class OrderAssigneeFactory(factory.django.DjangoModelFactory):
    """Order Assignee factory."""

    created_by = factory.SubFactory(AdviserFactory)
    order = factory.SubFactory(OrderFactory)
    adviser = factory.SubFactory(AdviserFactory)
    estimated_time = factory.Faker('random_int', min=10, max=100)

    class Meta:
        model = 'order.OrderAssignee'


class OrderAssigneeCompleteFactory(OrderAssigneeFactory):
    """Order Assignee factory with actual time set."""

    actual_time = factory.Faker('random_int', min=10, max=100)


class HourlyRateFactory(factory.django.DjangoModelFactory):
    """HourlyRate factory."""

    class Meta:
        model = 'order.HourlyRate'
