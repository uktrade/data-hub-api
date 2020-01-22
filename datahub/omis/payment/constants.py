from django.db import models
from model_utils import Choices


class PaymentGatewaySessionStatus(models.TextChoices):
    """Statuses for payment gateway sessions."""

    # Payment created; user has not yet visited the payment url
    CREATED = ('created', 'Created')
    # User has visited payment url and is entering payment details
    STARTED = ('started', 'Started')
    # User has submitted payment details but hasn't confirmed yet
    SUBMITTED = ('submitted', 'Submitted')
    # User successfully completed the payment
    SUCCESS = ('success', 'Success')
    # User attempted to make a payment but the payment did not complete
    FAILED = ('failed', 'Failed')
    # Payment cancelled by the system
    CANCELLED = ('cancelled', 'Cancelled')
    # Something went wrong with GOV.UK Pay
    ERROR = ('error', 'Error')


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
