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
from datahub.omis.order.utils import compose_official_address
from datahub.omis.quote.constants import (
    QUOTE_EXPIRY_DAYS_BEFORE_DELIVERY,
    QUOTE_EXPIRY_DAYS_FROM_NOW,
)

QUOTE_TEMPLATE = str(PurePath(__file__).parent / 'templates/content.md')


def escape_markdown(content, escape_html=True):
    """Escape markdown characters so that when it's interpreted
    the converted text is not a valid markdown text.

    :param escape_html: html chars are escaped if True.
        Django already escapes HTML chars automatically when rendering
        templates so in those cases escape_html cam be safely set to False
    """
    # escape all markdown chars (e.g. replace * with \*)
    content = re.sub(r'([~_\*#\(\)\[\]`\-\+\\])', r'\\\1', content)

    # replace consecutive spaces/tabs/new lines with one space only
    content = re.sub(r'\s+', r' ', content)

    # escape html
    if escape_html:
        content = html.escape(content)

    return content


def generate_quote_reference(order):
    """:returns: a random unused reference of form:
            <order.reference>/Q-<(2) lettes>/<(1) number> e.g. GEA962/16/Q-AB1
    :raises RuntimeError: if no reference can be generated.
    """
    from datahub.omis.quote.models import Quote

    def gen():
        return '{letters}{numbers}'.format(
            letters=get_random_string(length=2, allowed_chars='ACEFHJKMNPRTUVWXY'),
            numbers=get_random_string(length=1, allowed_chars='123456789'),
        )

    return generate_reference(model=Quote, gen=gen, prefix=f'{order.reference}/Q-')


def generate_quote_content(order, expires_on):
    """:returns: the content of the quote populated with the given order details."""
    company = order.company
    company_address = compose_official_address(company)
    company_address_formatted = ', '.join(
        field
        for field in (
            company_address.line_1,
            company_address.line_2,
            company_address.county,
            company_address.town,
            company_address.postcode,
            getattr(company_address.country, 'name', None),
        )
        if field
    )
    pricing = get_pricing_from_order(order, in_pence=False)
    lead_assignee = order.get_lead_assignee()

    return render_to_string(
        QUOTE_TEMPLATE,
        {
            'order_reference': escape_markdown(order.reference, escape_html=False),
            'company_name': escape_markdown(order.company.name, escape_html=False),
            'order_description': escape_markdown(order.description, escape_html=False),
            'order_delivery_date': order.delivery_date,
            'subtotal_cost': pricing.subtotal_cost,
            'quote_expires_on': expires_on,
            'company_address': escape_markdown(company_address_formatted, escape_html=False),
            'contact_name': escape_markdown(order.contact.name, escape_html=False),
            'contact_email': order.get_current_contact_email(),
            'generic_contact_email': settings.OMIS_GENERIC_CONTACT_EMAIL,
            'lead_assignee_name': escape_markdown(lead_assignee.adviser.name, escape_html=False),
        },
    )


def calculate_quote_expiry_date(order):
    """:returns: the calculated expiry date value for the quote attached to the order.
    At the moment it's whichever is earliest of
    [delivery date - x days] OR [date quote created + y days]
    """
    now_date = now().date()

    x_days_before_delivery = order.delivery_date - timedelta(
        days=QUOTE_EXPIRY_DAYS_BEFORE_DELIVERY,
    )

    y_days_from_now = now_date + timedelta(days=QUOTE_EXPIRY_DAYS_FROM_NOW)

    expiry_date = min(x_days_before_delivery, y_days_from_now)

    if expiry_date < now_date:
        raise ValidationError(
            {
                'delivery_date': [
                    'The calculated expiry date for the quote is in the past. '
                    'You might be able to fix this by changing the delivery date.',
                ],
            },
        )
    return expiry_date


def get_latest_terms_and_conditions():
    """:returns: the latest TermsAndConditions object if it exists, None otherwise."""
    from datahub.omis.quote.models import TermsAndConditions

    return TermsAndConditions.objects.order_by('-created_on').first()
