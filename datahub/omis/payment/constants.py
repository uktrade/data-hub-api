from django.db import models


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


class PaymentMethod(models.TextChoices):
    """Payment methods."""

    CARD = ('card', 'Card')
    BACS = ('bacs', 'BACS')
    CHEQUE = ('cheque', 'Cheque')
    MANUAL = ('manual', 'Manual')


class RefundStatus(models.TextChoices):
    """Refund statuses."""

    REQUESTED = ('requested', 'Requested')
    APPROVED = ('approved', 'Approved and Paid')
    REJECTED = ('rejected', 'Rejected')
