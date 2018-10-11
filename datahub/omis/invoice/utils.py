from datetime import timedelta

from datahub.omis.invoice.constants import (
    PAYMENT_DUE_DAYS_BEFORE_DELIVERY,
    PAYMENT_DUE_DAYS_FROM_NOW,
)


def calculate_payment_due_date(order):
    """
    :returns: the calculated payment due date value.
        At the moment it's whichever is earliest of
        [delivery date - x days] OR [date quote accepted + y days]

    The resulting date is not going to be in the past because the constants
    are so that there's always a gap between the quote expiry date
    and the payment due date.
    Given the quote expiry date as
        [delivery date - a days] OR [date quote created + y days]
    and payment due date as
        [delivery date - b days] OR [date quote accepted + y days]

    with a = 21, b = 14 and y = 30

    quote created < quote accepted <= quote expiry date < payment due date < delivery date
    and there is always a gap between the quote expiry date and the payment due date
    of at least 7 days.
    """
    x_days_before_delivery = (
        order.delivery_date - timedelta(days=PAYMENT_DUE_DAYS_BEFORE_DELIVERY)
    )

    y_days_from_acceptance = (
        order.quote.accepted_on.date() + timedelta(days=PAYMENT_DUE_DAYS_FROM_NOW)
    )

    return min(x_days_before_delivery, y_days_from_acceptance)
