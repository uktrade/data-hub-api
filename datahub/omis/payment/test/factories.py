import random
import uuid

import factory
from django.utils.timezone import utc

from datahub.company.test.factories import AdviserFactory
from datahub.omis.order.test.factories import OrderPaidFactory, OrderWithAcceptedQuoteFactory
from .. import constants
from ..models import RefundStatus


class PaymentFactory(factory.django.DjangoModelFactory):
    """Payment factory."""

    id = factory.LazyFunction(uuid.uuid4)
    order = factory.SubFactory(OrderPaidFactory)
    reference = factory.Faker('pystr')
    transaction_reference = factory.Faker('pystr')
    additional_reference = factory.Faker('pystr')
    amount = factory.Faker('random_int', max=100)
    method = constants.PaymentMethod.bacs
    received_on = factory.Faker('date')

    class Meta:
        model = 'omis-payment.Payment'


class PaymentGatewaySessionFactory(factory.django.DjangoModelFactory):
    """PaymentGatewaySession factory."""

    id = factory.LazyFunction(uuid.uuid4)
    order = factory.SubFactory(OrderWithAcceptedQuoteFactory)
    status = constants.PaymentGatewaySessionStatus.created
    govuk_payment_id = factory.Faker('pystr', min_chars=27, max_chars=27)

    class Meta:
        model = 'omis-payment.PaymentGatewaySession'


class RequestedRefundFactory(factory.django.DjangoModelFactory):
    """Factory for refund requested."""

    id = factory.LazyFunction(uuid.uuid4)
    created_by = factory.SubFactory(AdviserFactory)
    modified_by = factory.SubFactory(AdviserFactory)
    order = factory.SubFactory(OrderPaidFactory)
    reference = factory.Faker('pystr')
    status = RefundStatus.requested
    requested_on = factory.Faker('date_time', tzinfo=utc)
    requested_by = factory.SubFactory(AdviserFactory)
    refund_reason = factory.Faker('text')
    requested_amount = factory.LazyAttribute(
        lambda refund: random.randint(1, refund.order.total_cost)
    )

    class Meta:
        model = 'omis-payment.Refund'


class ApprovedRefundFactory(RequestedRefundFactory):
    """Factory for refund requested, approved and paid."""

    status = RefundStatus.approved

    level1_approved_on = factory.Faker('date_time', tzinfo=utc)
    level1_approved_by = factory.SubFactory(AdviserFactory)
    level1_approval_notes = factory.Faker('text')

    level2_approved_on = factory.Faker('date_time', tzinfo=utc)
    level2_approved_by = factory.SubFactory(AdviserFactory)
    level2_approval_notes = factory.Faker('text')

    method = constants.PaymentMethod.bacs

    vat_amount = factory.LazyAttribute(
        lambda refund: int(refund.requested_amount * 0.2)
    )
    net_amount = factory.LazyAttribute(
        lambda refund: refund.requested_amount - refund.vat_amount
    )
    total_amount = factory.LazyAttribute(
        lambda refund: refund.requested_amount
    )
    additional_reference = factory.Faker('pystr')


class RejectedRefundFactory(RequestedRefundFactory):
    """Factory for refund requested and rejected."""

    status = RefundStatus.rejected

    rejection_reason = factory.Faker('text')
