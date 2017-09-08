from model_utils import Choices


OrderStatus = Choices(
    ('draft', 'Draft'),
    (
        'quote_awaiting_acceptance',
        'Quote awaiting acceptance'
    ),
    ('quote_accepted', 'Quote accepted'),
    ('paid', 'Paid'),
    ('complete', 'Complete'),
    ('cancelled', 'Cancelled')
)
