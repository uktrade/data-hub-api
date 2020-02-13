import uuid

from django.conf import settings
from django.db import models

from datahub.omis.core.utils import generate_datetime_based_reference
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.validators import OrderInStatusSubValidator
from datahub.omis.payment.constants import PaymentGatewaySessionStatus
from datahub.omis.payment.govukpay import PayClient


class BasePaymentGatewaySessionManager(models.Manager):
    """Custom Payment Gateway Session Manager."""

    def create_from_order(self, order, attrs=None):
        """
        :param order: Order instance for this payment gateway session
        :param attrs: dict with any extra property to be set on the object

        :returns: Payment Gateway Session instance created
        :raises GOVUKPayAPIException: if there is a problem with GOV.UK Pay
        :raises Conflict: if the order is not in the allowed status
        """
        # refresh ongoing sessions for this order first of all
        for session in self.filter(order=order).ongoing().select_for_update():
            session.refresh_from_govuk_payment()

        # validate that the order is in `quote_accepted`
        order.refresh_from_db()
        validator = OrderInStatusSubValidator(
            allowed_statuses=(OrderStatus.QUOTE_ACCEPTED,),
        )
        validator(order=order)

        # lock order to avoid race conditions
        order.__class__.objects.select_for_update().get(pk=order.pk)

        # cancel other ongoing sessions
        for session in self.filter(order=order).ongoing():
            session.cancel()

        # create a new payment gateway session
        session_id = uuid.uuid4()

        pay = PayClient()
        govuk_payment = pay.create_payment(
            amount=order.total_cost,
            reference=f'{order.reference}-{str(session_id)[:8].upper()}',
            description=settings.GOVUK_PAY_PAYMENT_DESCRIPTION.format(
                reference=order.reference,
            ),
            return_url=settings.GOVUK_PAY_RETURN_URL.format(
                public_token=order.public_token,
                session_id=session_id,
            ),
        )

        session = self.create(
            id=session_id,
            order=order,
            govuk_payment_id=govuk_payment['payment_id'],
            **(attrs or {}),
        )

        return session


class PaymentGatewaySessionQuerySet(models.QuerySet):
    """Custom Payment Gateway Session QuerySet."""

    def ongoing(self):
        """
        :returns: only non-finished sessions
        """
        return self.filter(
            status__in=[
                PaymentGatewaySessionStatus.CREATED,
                PaymentGatewaySessionStatus.STARTED,
                PaymentGatewaySessionStatus.SUBMITTED,
            ],
        )


# We use this style because some of the methods make sense only on the manager
PaymentGatewaySessionManager = BasePaymentGatewaySessionManager.from_queryset(
    PaymentGatewaySessionQuerySet,
)


class PaymentManager(models.Manager):
    """Custom Payment Manager."""

    def create_from_order(self, order, by, attrs):
        """
        :param order: Order instance for this payment
        :param by: the Advisor who made the action
        :param attrs: attributes for the payment

        :returns: Payment object created
        """
        return self.create(
            **attrs,
            reference=generate_datetime_based_reference(self.model),
            order=order,
            created_by=by,
        )
