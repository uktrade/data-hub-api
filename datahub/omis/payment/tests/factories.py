import uuid
import factory

from datahub.omis.order.test.factories import OrderPaidFactory

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
    payment_received_on = factory.Faker('date_time')

    class Meta:  # noqa: D101
        model = 'omis-payment.Payment'
