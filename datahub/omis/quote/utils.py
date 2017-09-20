from datetime import timedelta
from pathlib import PurePath

from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from datahub.omis.core.utils import generate_reference
from datahub.omis.order.pricing import get_pricing_from_order

from .constants import QUOTE_EXPIRY_DAYS_BEFORE_DELIVERY, QUOTE_EXPIRY_DAYS_FROM_NOW


QUOTE_TEMPLATE = PurePath(__file__).parent / 'templates/content.md'


def generate_quote_reference(order):
    """
    :returns: a random unused reference of form:
            <order.reference>/Q-<(2) lettes>/<(1) number> e.g. GEA962/16/Q-AB1
    :raises RuntimeError: if no reference can be generated.
    """
    from .models import Quote

    def gen():
        return '{letters}{numbers}'.format(
            letters=get_random_string(length=2, allowed_chars='ACEFHJKMNPRTUVWXY'),
            numbers=get_random_string(length=1, allowed_chars='123456789')
        )
    return generate_reference(model=Quote, gen=gen, prefix=f'{order.reference}/Q-')


def generate_quote_content(order, expires_on):
    """
    :returns: the content of the quote populated with the given order details.
    """
    return render_to_string(
        QUOTE_TEMPLATE,
        {
            'order': order,
            'pound_pricing': get_pricing_from_order(order, in_pence=False),
            'expires_on': expires_on,
        }
    )


def calculate_quote_expiry_date(order):
    """
    :returns: the calculated expiry date value for the quote attached to the order.
        At the moment it's whichever is earliest of
        [delivery date - x days] OR [date quote created + y days]
    """
    now_date = now().date()

    x_days_before_delivery = (
        order.delivery_date - timedelta(days=QUOTE_EXPIRY_DAYS_BEFORE_DELIVERY)
    )

    y_days_from_now = (
        now_date + timedelta(days=QUOTE_EXPIRY_DAYS_FROM_NOW)
    )

    expiry_date = min(x_days_before_delivery, y_days_from_now)

    if expiry_date < now_date:
        raise ValidationError({
            'delivery_date': [
                'The calculated expiry date for the quote is in the past. '
                'You might be able to fix this by changing the delivery date.'
            ]
        })
    return expiry_date
