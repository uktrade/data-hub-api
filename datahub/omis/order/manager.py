from django.db import models

from .constants import OrderStatus


class OrderQuerySet(models.QuerySet):
    """Custom Order QuerySet."""

    def publicly_accessible(self):
        """
        Only returns the orders that can be safely be accessible by the end client.
        """
        return self.filter(
            status__in=(
                OrderStatus.quote_awaiting_acceptance,
                OrderStatus.quote_accepted,
                OrderStatus.paid,
                OrderStatus.complete,
            )
        )
