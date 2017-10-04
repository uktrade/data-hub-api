from datetime import datetime, timedelta

from django.utils.timezone import now

from datahub.omis.core.utils import generate_reference

from .constants import PAYMENT_DUE_DAYS_BEFORE_DELIVERY, PAYMENT_DUE_DAYS_FROM_NOW


def generate_invoice_number():
    """
    :returns: an unused invoice number
    :raises RuntimeError: if no reference can be generated.
    """
    from .models import Invoice

    current_date = now()
    prefix = datetime.strftime(current_date, '%Y%m%d')

    def gen():
        # the select_for_update + len reduces race conditions (do not use .count()).
        # The problem could still occur when creating the first invoice of the day
        # but it's unlikely and the whole transaction is atomic so it would not put
        # the db in an inconsistent state.
        start_count = len(
            Invoice.objects.select_for_update().filter(created_on__date=now().date())
        )

        while True:
            start_count += 1
            yield f'{start_count:04}'

    return generate_reference(
        model=Invoice, gen=gen().__next__, prefix=prefix, field='invoice_number'
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
