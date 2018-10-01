from model_utils import Choices


OrderStatus = Choices(
    ('draft', 'Draft'),
    (
        'quote_awaiting_acceptance',
        'Quote awaiting acceptance',
    ),
    ('quote_accepted', 'Quote accepted'),
    ('paid', 'Paid'),
    ('complete', 'Complete'),
    ('cancelled', 'Cancelled'),
)


DEFAULT_HOURLY_RATE = '7e1ca5c3-dc5a-e511-9d3c-e4115bead28a'


VATStatus = Choices(
    ('uk', 'UK'),
    ('eu', 'EU excluding the UK'),
    ('outside_eu', 'Outside the EU'),
)
