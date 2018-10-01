import pytest

from datahub.omis.quote.test.factories import CancelledQuoteFactory
from .factories import OrderFactory
from ..constants import OrderStatus
from ..models import Order


pytestmark = pytest.mark.django_db


class TestOrderManager:
    """Tests for the Order Manager."""

    @pytest.mark.parametrize(
        'include_reopened', (False, True),
    )
    def test_publicly_accessible(self, include_reopened):
        """
        Test that `publicly_accessible()` only returns the publicly accessible orders.
        """
        # set up db
        for order_status_choice in OrderStatus:
            order_status = order_status_choice[0]
            OrderFactory(
                status=order_status,
                reference=f'{order_status}',
            )
        OrderFactory(
            status=OrderStatus.draft,
            quote=CancelledQuoteFactory(),
            reference='draft_with_cancelled_quote',
        )

        # define expectation
        expected_orders = {
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
        }
        if include_reopened:
            expected_orders.add('draft_with_cancelled_quote')

        # get result
        publicly_accessible_qs = Order.objects.publicly_accessible(
            include_reopened=include_reopened,
        )
        publicly_accessible_refs = set(publicly_accessible_qs.values_list('reference', flat=True))
        assert publicly_accessible_refs == expected_orders
