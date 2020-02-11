from django.db import models


class OrderStatus(models.TextChoices):
    """Order statuses."""

    DRAFT = ('draft', 'Draft')
    QUOTE_AWAITING_ACCEPTANCE = (
        'quote_awaiting_acceptance',
        'Quote awaiting acceptance',
    )
    QUOTE_ACCEPTED = ('quote_accepted', 'Quote accepted')
    PAID = ('paid', 'Paid')
    COMPLETE = ('complete', 'Complete')
    CANCELLED = ('cancelled', 'Cancelled')


DEFAULT_HOURLY_RATE = '7e1ca5c3-dc5a-e511-9d3c-e4115bead28a'


class VATStatus(models.TextChoices):
    """VAT statuses for orders."""

    UK = ('uk', 'UK')
    EU = ('eu', 'EU excluding the UK')
    OUTSIDE_EU = ('outside_eu', 'Outside the EU')
