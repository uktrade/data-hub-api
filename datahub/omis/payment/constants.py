from model_utils import Choices


PaymentMethod = Choices(
    ('card', 'Card'),
    ('bacs', 'BACS'),
    ('cheque', 'Cheque'),
    ('manual', 'Manual'),
)


RefundStatus = Choices(
    ('requested', 'Requested'),
    ('approved', 'Approved and Paid'),
    ('rejected', 'Rejected'),
)
