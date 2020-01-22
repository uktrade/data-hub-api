from django.db import models

from datahub.omis.order.constants import OrderStatus


class OrderQuerySet(models.QuerySet):
    """Custom Order QuerySet."""

    def publicly_accessible(self, include_reopened=False):
        """
        Only returns the orders that can be safely be accessible by the end client.

        :param include_reopened: if True, it includes orders in draft with cancelled
            quote
        """
        q = models.Q(
            status__in=(
                OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
                OrderStatus.QUOTE_ACCEPTED,
                OrderStatus.PAID,
                OrderStatus.COMPLETE,
            ),
        )
        if include_reopened:
            q = q | models.Q(
                status=OrderStatus.DRAFT,
                quote__cancelled_on__isnull=False,
            )

        return self.filter(q)
