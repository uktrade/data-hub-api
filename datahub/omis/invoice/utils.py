from datetime import datetime

from django.utils.timezone import now

from datahub.omis.core.utils import generate_reference


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
