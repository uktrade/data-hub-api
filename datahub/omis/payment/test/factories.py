import uuid

import factory

from datahub.omis.order.test.factories import OrderPaidFactory, OrderWithAcceptedQuoteFactory
from .. import constants


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
