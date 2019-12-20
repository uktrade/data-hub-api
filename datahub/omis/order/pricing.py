from collections import namedtuple

from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from datahub.omis.order.constants import VATStatus
from datahub.omis.order.validators import VATSubValidator


OrderPricing = namedtuple(
    'OrderPricing',
    ('net_cost', 'subtotal_cost', 'vat_cost', 'total_cost'),
)

ZERO_PRICING = OrderPricing(0, 0, 0, 0)


def get_pricing_from_order(order, in_pence=True):
    """
    :returns: an instance of OrderPricing from the obj `order`
    """
    if in_pence:
        transform = lambda x: x  # noqa: E731
    else:
        transform = lambda x: x / 100  # noqa: E731

    return OrderPricing(
        transform(order.net_cost),
        transform(order.subtotal_cost),
        transform(order.vat_cost),
        transform(order.total_cost),
    )


def _validate_vat(order):
    """
    Validate that the order has all the VAT fields required.

    :raises ValidationError: if not
    """
    validator = VATSubValidator()
    validator(order=order)


def can_pricing_be_calculated(order):
    """
    :returns: True if the pricing for `order` can be calculated
        (e.g. all the fields required are filled in)
    """
    try:
        _validate_vat(order)
    except ValidationError:
        return False
    return True


def should_vat_be_applied(order):
    """
    The logic is the following:
        - if VATStatus is uk => the VAT is always applied
        - if VATStatus is outside_eu => the VAT is never applied
        - if VATStatus is eu
            - if the VAT has been verified => the VAT is not applied
            - if the VAT has not been verified => the VAT is applied

    :returns: True if the VAT should be applied when calculating the pricing
    """
    _validate_vat(order)

    if order.vat_status == VATStatus.uk:
        return True
    if order.vat_status == VATStatus.outside_eu:
        return False

    assert order.vat_status == VATStatus.eu
    return not order.vat_verified


def _calculate_pricing(estimated_time, hourly_rate, vat_value, discount_value):
    """
    Calculate the pricing using the given base values.

    :param estimated_time: time needed to complete the order in minutes (e.g. 60 is 1 hour)
    :param hourly rate: hourly charges for the OMIS services in pence (e.g. 100 is £1)
    :param vat_value: the VAT percentage value to apply (e.g. 19.5 is 19.5% of the amount)
    :param discount_value: the discount value to subtract in pence (e.g. 100 is £1)

    :returns: pricing values as integers (in pence)
    """
    if estimated_time == 0:
        return ZERO_PRICING

    # convert minutes to hours and calculate the overall net cost
    # the formula is: (hourly rate * total hours required)
    # the result is an integer (money in pence) so we round up or down
    net_cost = round((estimated_time / 60) * hourly_rate)

    # subtract potential discount defaulting to 0 if the overall value is negative
    subtotal_cost = max(net_cost - discount_value, 0)

    # apply VAT to subtotal, `vat_value` is a Decimal so we need to cast to float first
    # the formula is: (vat value * subtotal) / 100
    # the result is an integer (money in pence) so we round up or down
    vat_cost = round(float(vat_value) * subtotal_cost * 0.01)

    # total is subtotal + vat cost
    total_cost = subtotal_cost + vat_cost

    return OrderPricing(net_cost, subtotal_cost, vat_cost, total_cost)


def calculate_order_pricing(order):
    """
    :returns: the pricing for `order`
    """
    if not can_pricing_be_calculated(order):
        return ZERO_PRICING

    tot_estimated_time = order.assignees.aggregate(sum=Sum('estimated_time'))['sum'] or 0

    if should_vat_be_applied(order):
        vat_value = order.hourly_rate.vat_value
    else:
        vat_value = 0

    return _calculate_pricing(
        estimated_time=tot_estimated_time,
        hourly_rate=order.hourly_rate.rate_value,
        vat_value=vat_value,
        discount_value=order.discount_value,
    )


def update_order_pricing(order, commit=True):
    """
    Change the order model by updating the pricing fields.
    If commit = True, commit the changes to the db as well.
    """
    original_pricing = get_pricing_from_order(order)
    new_pricing = calculate_order_pricing(order)

    # avoid an update if the pricing hasn't changed
    if original_pricing == new_pricing:
        return

    order.net_cost = new_pricing.net_cost
    order.subtotal_cost = new_pricing.subtotal_cost
    order.vat_cost = new_pricing.vat_cost
    order.total_cost = new_pricing.total_cost

    if commit:
        order.save()
