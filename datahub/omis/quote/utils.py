import html
import re
from datetime import timedelta
from pathlib import PurePath

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

from datahub.omis.core.utils import generate_reference
from datahub.omis.order.pricing import get_pricing_from_order

from .constants import QUOTE_EXPIRY_DAYS_BEFORE_DELIVERY, QUOTE_EXPIRY_DAYS_FROM_NOW


QUOTE_TEMPLATE = PurePath(__file__).parent / 'templates/content.md'


def escape_markdown(content):
    """
    Escape markdown characters so that when it's interpreted
    the converted text is not a valid markdown text.
    """
    # escape all markdown chars (e.g. replace * with \*)
    content = re.sub(r'([~_\*#\(\)\[\]`\-\+\\])', r'\\\1', content)

    # replace consecutive spaces/tabs/new lines with one space only
    content = re.sub(r'\s+', r' ', content)

    # escape html
    content = html.escape(content)

    return content


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
    company = order.company
    company_address = ', '.join(
        field for field in (
            company.registered_address_1,
            company.registered_address_2,
            company.registered_address_county,
            company.registered_address_town,
            company.registered_address_postcode,
            getattr(company.registered_address_country, 'name', None)
        )
        if field
    )
    pricing = get_pricing_from_order(order, in_pence=False)
    lead_assignee = order.get_lead_assignee()

    return render_to_string(
        QUOTE_TEMPLATE,
        {
            'order_reference': escape_markdown(order.reference),
            'company_name': escape_markdown(order.company.name),
            'order_description': escape_markdown(order.description),
            'order_delivery_date': order.delivery_date,
            'subtotal_cost': pricing.subtotal_cost,
            'quote_expires_on': expires_on,
            'company_address': escape_markdown(company_address),
            'contact_name': escape_markdown(order.contact.name),
            'contact_email': order.get_current_contact_email(),
            'generic_contact_email': settings.OMIS_GENERIC_CONTACT_EMAIL,
            'lead_assignee_name': escape_markdown(lead_assignee.adviser.name)
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


def get_latest_terms_and_conditions():
    """
    :returns: the latest TermsAndConditions object if it exists, None otherwise.
    """
    from .models import TermsAndConditions

    return TermsAndConditions.objects.order_by('-created_on').first()
