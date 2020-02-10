from decimal import Decimal
from unittest import mock

import pytest
from rest_framework.exceptions import ValidationError

from datahub.omis.order.constants import VATStatus
from datahub.omis.order.models import Order
from datahub.omis.order.pricing import (
    _calculate_pricing,
    calculate_order_pricing,
    can_pricing_be_calculated,
    get_pricing_from_order,
    OrderPricing,
    should_vat_be_applied,
    update_order_pricing, ZERO_PRICING,
)
from datahub.omis.order.test.factories import HourlyRateFactory, OrderAssigneeFactory, OrderFactory


class TestGetPricingFromOrder:
    """Tests for the get_pricing_from_order function."""

    def test_in_pence(self):
        """
        Test converting the pricing of an order to an OrderPricing obj with
        values defined in pence.
        """
        order = Order(
            net_cost=1101,
            subtotal_cost=1001,
            vat_cost=302,
            total_cost=1303,
        )
        pricing = get_pricing_from_order(order, in_pence=True)
        assert pricing.net_cost == 1101
        assert pricing.subtotal_cost == 1001
        assert pricing.vat_cost == 302
        assert pricing.total_cost == 1303

    def test_in_pound(self):
        """
        Test converting the pricing of an order to an OrderPricing obj with
        values defined in pound.
        """
        order = Order(
            net_cost=1101,
            subtotal_cost=1001,
            vat_cost=302,
            total_cost=1303,
        )
        pricing = get_pricing_from_order(order, in_pence=False)
        assert pricing.net_cost == 11.01
        assert pricing.subtotal_cost == 10.01
        assert pricing.vat_cost == 3.02
        assert pricing.total_cost == 13.03


class TestCanPricingBeCalculated:
    """Tests for the can_pricing_be_calculated function."""

    @pytest.mark.parametrize(
        'fields',
        (
            {'vat_status': None, 'vat_number': '123'},
            {'vat_status': None, 'vat_verified': True},
            {'vat_status': None, 'vat_number': '123', 'vat_verified': True},
            {'vat_status': VATStatus.EU, 'vat_number': '', 'vat_verified': None},
            {'vat_status': VATStatus.EU, 'vat_number': '', 'vat_verified': True},
        ),
    )
    def test_cannot_with_incomplete_vat_data(self, fields):
        """
        Test that it returns False if the VAT fields are incomplete.
        """
        order = Order(**fields)
        assert not can_pricing_be_calculated(order)

    @pytest.mark.parametrize(
        'fields',
        (
            {'vat_status': VATStatus.OUTSIDE_EU},
            {'vat_status': VATStatus.UK},
            {'vat_status': VATStatus.EU, 'vat_number': '', 'vat_verified': False},
        ),
    )
    def test_can(self, fields):
        """Test that it returns True if the VAT fields are filled in."""
        order = Order(**fields)
        assert can_pricing_be_calculated(order)


class TestShouldVATBeApplied:
    """Tests for the should_vat_be_applied function."""

    def test_incomplete_raises_exception(self):
        """
        Test that if the order doesn't have the right VAT fields populated,
        it raises a ValidationError.
        """
        order = Order(vat_status=None)

        with pytest.raises(ValidationError):
            should_vat_be_applied(order)

    @pytest.mark.parametrize(
        'fields',
        (
            {'vat_status': VATStatus.OUTSIDE_EU},
            {'vat_status': VATStatus.EU, 'vat_verified': True, 'vat_number': '123'},
        ),
    )
    def test_shouldnt(self, fields):
        """Test the cases where the VAT should not be applied."""
        order = Order(**fields)
        assert not should_vat_be_applied(order)

    @pytest.mark.parametrize(
        'fields',
        (
            {'vat_status': VATStatus.UK},
            {'vat_status': VATStatus.EU, 'vat_verified': False},
        ),
    )
    def test_should(self, fields):
        """Test the cases where the VAT should be applied."""
        order = Order(**fields)
        assert should_vat_be_applied(order)


class TestCalculatePricing:
    """Tests for the _calculate_pricing function."""

    def test_zero_hours(self):
        """
        Test that given estimated time = 0, all the calculated values are zero.
        """
        pricing = _calculate_pricing(
            estimated_time=0,
            hourly_rate=1000,
            vat_value=Decimal(20),
            discount_value=100,
        )
        assert pricing == OrderPricing(0, 0, 0, 0)

    def test_with_vat(self):
        """
        Test that given
            hourly rate: 1000 pence
            vat rate: 19.5

            estimated time: 130 mins
            discount amount: 100 pence

        The calculations are:

            net cost: time * hourly rate
                => 2166.6666 rounded up to 2167
            subtotal cost: net cost - discount amount
                => 2067
            vat cost: 19.5% of subtotal
                => 403.065 rounded down to 403
            total cost: subtotal cost + vat cost
                => 2470
        """
        pricing = _calculate_pricing(
            estimated_time=130,
            hourly_rate=1000,
            vat_value=Decimal(19.5),
            discount_value=100,
        )
        assert pricing.net_cost == 2167
        assert pricing.subtotal_cost == 2067
        assert pricing.vat_cost == 403
        assert pricing.total_cost == 2470

    def test_without_vat(self):
        """
        Test that given
            hourly rate: 1000 pence
            vat rate: 0

            estimated time: 130 mins
            discount amount: 100 pence

        The calculations are:

            net cost: time * hourly rate
                => 2166.6666 rounded up to 2167
            subtotal cost: net cost - discount amount
                => 2067
            vat cost: 0% of subtotal
                => 0
            total cost: subtotal cost + vat cost
                => 2067
        """
        pricing = _calculate_pricing(
            estimated_time=130,
            hourly_rate=1000,
            vat_value=0,
            discount_value=100,
        )
        assert pricing.net_cost == 2167
        assert pricing.subtotal_cost == 2067
        assert pricing.vat_cost == 0
        assert pricing.total_cost == 2067


@pytest.mark.django_db
class TestCalculateOrderPricing:
    """Tests for the calculate_order_pricing function."""

    def test_zero_if_order_incomplete(self):
        """
        Test that if an order doesn't have all the VAT fields, the pricing is zero.
        """
        order = Order(vat_status=None)
        pricing = calculate_order_pricing(order)

        assert pricing == ZERO_PRICING

    def test_zero_with_no_estimated_time(self):
        """
        Test that if an order doesn't have any assignees, the pricing is zero.
        """
        order = OrderFactory(assignees=[])
        assert not order.assignees.count()

        order = Order(vat_status=None)
        pricing = calculate_order_pricing(order)

        assert pricing == ZERO_PRICING

    @pytest.mark.parametrize(
        'fields',
        (
            {'vat_status': VATStatus.UK},
            {'vat_status': VATStatus.EU, 'vat_verified': False},
        ),
    )
    def test_with_applied_vat(self, fields):
        """Test when the VAT status requires the VAT to be applied."""
        hourly_rate = HourlyRateFactory(rate_value=110, vat_value=Decimal(19.5))
        order = OrderFactory(
            **fields,
            discount_value=100,
            hourly_rate=hourly_rate,
            assignees=[],
        )
        OrderAssigneeFactory(order=order, estimated_time=140)

        pricing = calculate_order_pricing(order)

        assert pricing.net_cost == 257
        assert pricing.subtotal_cost == 157
        assert pricing.vat_cost == 31
        assert pricing.total_cost == 188

    @pytest.mark.parametrize(
        'fields',
        (
            {'vat_status': VATStatus.OUTSIDE_EU},
            {'vat_status': VATStatus.EU, 'vat_verified': True},
        ),
    )
    def test_without_applied_vat(self, fields):
        """Test when the VAT status doesn't require the VAT to be applied."""
        hourly_rate = HourlyRateFactory(rate_value=110, vat_value=Decimal(19.5))
        order = OrderFactory(
            **fields,
            discount_value=100,
            hourly_rate=hourly_rate,
            assignees=[],
        )
        OrderAssigneeFactory(order=order, estimated_time=140)

        pricing = calculate_order_pricing(order)

        assert pricing.net_cost == 257
        assert pricing.subtotal_cost == 157
        assert pricing.vat_cost == 0
        assert pricing.total_cost == 157


@pytest.mark.django_db
class TestUpdateOrderPricing:
    """Tests for the update_order_pricing function."""

    def test_without_committing(self):
        """
        Test that if udpate_order_pricing is called without committing,
        the order model is changed but not the db.
        """
        order = OrderFactory(vat_status=VATStatus.UK)
        orig_total_cost = order.total_cost

        # change order and recalculate pricing without saving
        order.vat_status = VATStatus.OUTSIDE_EU
        update_order_pricing(order, commit=False)

        assert order.total_cost != orig_total_cost

        # refresh and check that it hasn't changed
        order.refresh_from_db()
        assert order.total_cost == orig_total_cost

    def test_with_commit(self):
        """
        Test that if udpate_order_pricing is called with commit = True,
        the order model is changed and the db as well.
        """
        order = OrderFactory(vat_status=VATStatus.UK)
        orig_total_cost = order.total_cost

        # change order and recalculate pricing without saving
        order.vat_status = VATStatus.OUTSIDE_EU
        update_order_pricing(order, commit=True)

        assert order.total_cost != orig_total_cost

        # refresh and check that it changed
        order.refresh_from_db()
        assert order.total_cost != orig_total_cost

    def test_doesnt_save_if_pricing_didnt_change(self):
        """
        Test that if the pricing didn't change, update_order_pricing doesn't
        do anything.
        """
        order = OrderFactory()
        with mock.patch.object(order, 'save') as mocked_save:
            assert order.total_cost > 0

            order.description = 'updated description'
            update_order_pricing(order, commit=True)

            assert not mocked_save.called
