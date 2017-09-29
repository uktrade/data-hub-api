import pytest

from .factories import OrderFactory
from ..constants import OrderStatus
from ..models import Order


pytestmark = pytest.mark.django_db


class TestOrderManager:
    """Tests for the Order Manager."""

    def test_publicly_accessible(self):
        """
        Test that `publicly_accessible()` only returns the publicly accessible orders.
        """
        for order_status_choice in OrderStatus:
            order_status = order_status_choice[0]
            OrderFactory(
                status=order_status,
                reference=f'{order_status}'
            )

        publicly_accessible_qs = Order.objects.publicly_accessible()
        publicly_accessible_refs = set(publicly_accessible_qs.values_list('reference', flat=True))

        assert publicly_accessible_refs == {
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
        }
