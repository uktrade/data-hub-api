import pytest

from datahub.omis.order.constants import VATStatus
from datahub.omis.order.pricing import get_pricing_from_order
from datahub.omis.order.test.factories import OrderAssigneeFactory, OrderFactory


pytestmark = pytest.mark.django_db


class TestUpdateOrderPricingPreSave:
    """Tests for the update_order_pricing_on_pre_order_save signal receiver."""

    def test_pricing_updated_on_order_save(self):
        """
        Test that if an order is saved, the related pricing is recalculated and
        the order updated.
        """
        order = OrderFactory(vat_status=VATStatus.UK, discount_value=0)
        assert order.vat_cost > 0

        order.vat_status = VATStatus.OUTSIDE_EU
        order.save()

        order.refresh_from_db()
        assert order.vat_cost == 0

    def test_pricing_unchanged_if_update_unrelated(self):
        """
        Test that if an unrelated field gets updated, the pricing stays the same.
        """
        order = OrderFactory()
        pre_update_pricing = get_pricing_from_order(order)

        order.description = 'updated description'
        order.save()

        order.refresh_from_db()
        post_update_pricing = get_pricing_from_order(order)

        assert pre_update_pricing == post_update_pricing


class TestUpdateOrderPricingOnRelatedObjSave:
    """Tests for the update_order_pricing_on_related_obj_save logic."""

    def test_pricing_update_on_assignee_created(self):
        """Test that if a new assignee is added, the pricing on the order changes."""
        order = OrderFactory(discount_value=0)
        assert order.total_cost > 0
        pre_update_total_cost = order.total_cost

        OrderAssigneeFactory(order=order)

        order.refresh_from_db()
        assert order.total_cost > 0
        post_update_total_cost = order.total_cost

        assert pre_update_total_cost != post_update_total_cost

    def test_pricing_updated_on_assignee_updated(self):
        """Test that if an assignee is updated, the pricing on the order changes."""
        order = OrderFactory(discount_value=0)
        assert order.total_cost > 0
        pre_update_total_cost = order.total_cost

        assignee = order.assignees.first()
        assignee.estimated_time += 100
        assignee.save()

        order.refresh_from_db()
        assert order.total_cost > 0
        post_update_total_cost = order.total_cost

        assert pre_update_total_cost != post_update_total_cost

    def test_pricing_updated_on_assignee_deleted(self):
        """Test that if an assignee is deleted, the pricing on the order changes."""
        order = OrderFactory(discount_value=0)
        assert order.total_cost > 0
        pre_update_total_cost = order.total_cost

        assignee = order.assignees.first()
        assignee.delete()

        order.refresh_from_db()
        post_update_total_cost = order.total_cost

        assert pre_update_total_cost != post_update_total_cost

    def test_pricing_unchanged_if_update_unrelated(self):
        """
        Test that if an assignee is changed in an unrelated way,
        the pricing on the order doesn't change.
        """
        order = OrderFactory(discount_value=0)
        assert order.total_cost > 0
        pre_update_total_cost = order.total_cost

        assignee = order.assignees.first()
        assignee.is_lead = not assignee.is_lead
        assignee.save()

        order.refresh_from_db()
        assert order.total_cost > 0
        post_update_total_cost = order.total_cost

        assert pre_update_total_cost == post_update_total_cost
