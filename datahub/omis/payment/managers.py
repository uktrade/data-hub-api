from django.db import models

from datahub.omis.core.utils import generate_datetime_based_reference


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
            created_by=by
        )
