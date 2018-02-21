from model_utils import Choices


PaymentGatewaySessionStatus = Choices(
    ('created', 'Created'),  # Payment created; user has not yet visited the payment url
    ('started', 'Started'),  # User has visited payment url and is entering payment details
    ('submitted', 'Submitted'),  # User has submitted payment details but hasn't confirmed yet
    ('success', 'Success'),  # User successfully completed the payment
    ('failed', 'Failed'),  # User attempted to make a payment but the payment did not complete
    ('cancelled', 'Cancelled'),  # Payment cancelled by the system
    ('error', 'Error'),  # Something went wrong with GOV.UK Pay
)


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
