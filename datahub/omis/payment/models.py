import uuid

from django.conf import settings
from django.db import models, transaction

from datahub.core.models import BaseModel
from datahub.omis.core.utils import generate_datetime_based_reference
from datahub.omis.payment.constants import PaymentGatewaySessionStatus, PaymentMethod, RefundStatus
from datahub.omis.payment.govukpay import PayClient
from datahub.omis.payment.managers import PaymentGatewaySessionManager, PaymentManager
from datahub.omis.payment.utils import trasform_govuk_payment_to_omis_payment_data

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class PaymentGatewaySession(BaseModel):
    """Details of a payment-by-card session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='payment_gateway_sessions',
    )
    status = models.CharField(
        max_length=100,
        choices=PaymentGatewaySessionStatus.choices,
        default=PaymentGatewaySessionStatus.CREATED,
    )
    govuk_payment_id = models.CharField(
        max_length=100,
        verbose_name='GOV.UK payment ID',
    )

    objects = PaymentGatewaySessionManager()

    class Meta:
        db_table = 'omis-payment_paymentgatewaysession'
        ordering = ('-created_on',)

    def __str__(self):
        """Human-readable representation."""
        return f'Payment gateway session {self.id} for order {self.order}'

    def _get_payment_from_govuk_pay(self):
        """:returns: the GOV.UK payment data for this payment gateway session

        :raises GOVUKPayAPIException: if there is a problem with GOV.UK Pay
        """
        return PayClient().get_payment_by_id(self.govuk_payment_id)

    def get_payment_url(self):
        """:returns: the GOV.UK Pay payment url to redirect the users to complete the payment

        :raises GOVUKPayAPIException: if there is a problem with GOV.UK Pay
        """
        if self.is_finished():
            return ''

        next_url = self._get_payment_from_govuk_pay()['_links']['next_url'] or {}
        return next_url.get('href', '')

    def is_finished(self):
        """:returns: True if this payment gateway session is in a finished status"""
        return self.status in (
            PaymentGatewaySessionStatus.SUCCESS,
            PaymentGatewaySessionStatus.FAILED,
            PaymentGatewaySessionStatus.CANCELLED,
            PaymentGatewaySessionStatus.ERROR,
        )

    @transaction.atomic
    def refresh_from_govuk_payment(self):
        """Refreshes this record with the data from the related GOV.UK payment.
        If, during the update, the GOV.UK response says that the payment happened
        successfully, the related order gets marked as `paid` and an
        `payment.Payment` record is created from the GOV.UK payment data.

        :returns: True if the record needed and got refreshed, False otherwise

        :raises GOVUKPayAPIException: if there is a problem with GOV.UK Pay

        Note: this should be the only method changing the status of this session object.
        """
        if self.is_finished():  # no need to refresh
            return False

        govuk_payment = self._get_payment_from_govuk_pay()
        new_status = govuk_payment['state']['status']
        if new_status == self.status:  # no changes made
            return False

        self.status = new_status
        self.save()

        if self.status == PaymentGatewaySessionStatus.SUCCESS:
            self.order.mark_as_paid(
                by=None,
                payments_data=[
                    trasform_govuk_payment_to_omis_payment_data(govuk_payment),
                ],
            )
        return True

    def cancel(self):
        """Cancels this payment gateway session and the related GOV.UK payment.

        :raises GOVUKPayAPIException: if there is a problem with GOV.UK Pay
        """
        PayClient().cancel_payment(self.govuk_payment_id)
        self.refresh_from_govuk_payment()


class Payment(BaseModel):
    """Details of a payment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )
    reference = models.CharField(
        max_length=100,
        help_text='Autogenerated by the system.',
    )
    transaction_reference = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        help_text='As it appears on the transaction receipt.',
    )
    additional_reference = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        editable=True,
        help_text='Legacy field.',
    )

    amount = models.PositiveIntegerField(help_text='Amount paid in pence.')
    method = models.CharField(
        max_length=100,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BACS,
    )
    received_on = models.DateField()

    # card payments
    cardholder_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    card_brand = models.CharField(max_length=100, blank=True)
    billing_email = models.EmailField(blank=True)
    billing_phone = models.CharField(max_length=100, blank=True)
    billing_fax = models.CharField(max_length=100, blank=True)
    billing_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_postcode = models.CharField(max_length=100, blank=True)
    billing_address_country = models.CharField(max_length=MAX_LENGTH, blank=True)

    # cheque
    cheque_number = models.CharField(max_length=MAX_LENGTH, blank=True)
    giro_slip_number = models.CharField(max_length=MAX_LENGTH, blank=True)
    sort_code = models.CharField(max_length=100, blank=True)
    cheque_banked_on = models.DateTimeField(blank=True, null=True)
    cheque_paid_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    objects = PaymentManager()

    class Meta:
        db_table = 'omis-payment_payment'
        ordering = ('created_on',)

    def __str__(self):
        """Human-readable representation."""
        return self.reference


class Refund(BaseModel):
    """Details of a refund."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )
    reference = models.CharField(max_length=100)
    status = models.CharField(max_length=100, choices=RefundStatus.choices)

    requested_on = models.DateTimeField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    refund_reason = models.TextField(blank=True)
    requested_amount = models.PositiveIntegerField(
        help_text='In pence. E.g. £10 should be 1000.',
    )

    level1_approved_on = models.DateTimeField(blank=True, null=True)
    level1_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    level1_approval_notes = models.TextField(blank=True)

    level2_approved_on = models.DateTimeField(blank=True, null=True)
    level2_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='+',
    )
    level2_approval_notes = models.TextField(blank=True)

    method = models.CharField(  # noqa: DJ001
        max_length=100,
        null=True,
        blank=True,
        choices=PaymentMethod.choices,
    )
    net_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='In pence. E.g. £10 should be 1000.',
    )
    vat_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='In pence. E.g. £10 should be 1000.',
    )
    total_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='In pence. E.g. £10 should be 1000.',
    )

    rejection_reason = models.TextField(blank=True)

    # legacy fields
    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    additional_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'omis-payment_refund'
        ordering = ('created_on',)

    def __str__(self):
        """Human-readable representation."""
        return f'{self.reference} for order {self.order}'

    def save(self, *args, **kwargs):
        """Generate a reference if necessary."""
        if not self.reference:
            self.reference = generate_datetime_based_reference(self.__class__, field='reference')
        super().save(*args, **kwargs)
