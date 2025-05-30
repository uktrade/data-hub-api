import secrets
import uuid
from datetime import datetime, time, timezone
from enum import StrEnum
from functools import partial

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from mptt.fields import TreeForeignKey

from datahub.company.models import Advisor, Company, Contact
from datahub.company_activity.models import CompanyActivity
from datahub.core import reversion
from datahub.core.models import (
    BaseConstantModel,
    BaseModel,
    BaseOrderedConstantModel,
)
from datahub.core.utils import get_front_end_url
from datahub.metadata.models import Country, Sector, Team, UKRegion
from datahub.omis.core.utils import generate_reference
from datahub.omis.invoice.models import Invoice
from datahub.omis.order import validators
from datahub.omis.order.constants import DEFAULT_HOURLY_RATE, OrderStatus, VATStatus
from datahub.omis.order.managers import OrderQuerySet
from datahub.omis.order.signals import (
    order_cancelled,
    order_completed,
    order_paid,
    quote_accepted,
    quote_cancelled,
    quote_generated,
)
from datahub.omis.order.utils import populate_billing_data
from datahub.omis.payment.models import Payment
from datahub.omis.payment.validators import ReconcilablePaymentsSubValidator
from datahub.omis.quote.models import Quote

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class ServiceType(BaseOrderedConstantModel):
    """Order service type.
    E.g. 'Validated contacts', 'Event', 'Market Research'.
    """


class HourlyRate(BaseConstantModel):
    """Values for the hourly rates used to calculate order pricing and for the
    current VAT to apply.
    """

    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    rate_value = models.PositiveIntegerField(
        help_text='Rate in pence. E.g. 1 pound should be stored as 100 (100 pence).',
    )
    vat_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='VAT to apply as percentage value (0.00 to 100.00).',
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    class Meta(BaseConstantModel.Meta):
        db_table = 'omis-order_hourlyrate'


class CancellationReason(BaseOrderedConstantModel):
    """Reasons for cancelling an order."""


class OrderPermission(StrEnum):
    """Order permission codename constants."""

    view = 'view_order'
    add = 'add_order'
    change = 'change_order'
    delete = 'delete_order'
    export = 'export_order'


@reversion.register_base_model()
class Order(BaseModel):
    """Details regarding an OMIS Order.

    States:

        Draft (OrderStatus.DRAFT)
            An order is created by one or more DIT advisers to holds the details
            of the service offered to a specific contact (the client).
            An order can stay in draft for as long as needed if the details have not
            been defined yet.
        Quote sent / awaiting acceptance (OrderStatus.QUOTE_AWAITING_ACCEPTANCE)
            When the details have been defined and the related information filled in,
            a quote can be generated by the adviser.
            After this point, the order becomes readonly and the client is asked to approve it.
            The DIT adviser can still reopen the order and cancel the quote.
            A new quote would have to be generated, sent and accepted by the client in this case.
        Quote accepted (OrderStatus.QUOTE_ACCEPTED)
            After accepting the quote, the client receives an invoice and is asked to pay.
            At this point but before paying, the order can still be reopened and
            the quote cancelled.
            A new quote would have to be generated, sent and accepted by the client in this case.
        Paid (OrderStatus.PAID)
            The contact pays for the order. After this point, the order cannot be reopened.
        Complete (OrderStatus.COMPLETE)
            The DIT adviser delivers the service.
        Cancelled (OrderStatus.CANCELLED)
            The order has been cancelled.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reference = models.CharField(max_length=100)
    public_token = models.CharField(
        max_length=100,
        unique=True,
        help_text='Used for public facing access.',
    )

    status = models.CharField(
        max_length=100,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
    )

    company = models.ForeignKey(
        Company,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )
    contact = models.ForeignKey(
        Contact,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
    )

    primary_market = models.ForeignKey(
        Country,
        related_name='%(class)ss',
        null=True,
        on_delete=models.SET_NULL,
    )
    sector = TreeForeignKey(
        Sector,
        related_name='+',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    uk_region = models.ForeignKey(
        UKRegion,
        related_name='%(class)ss',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    service_types = models.ManyToManyField(
        ServiceType,
        related_name='%(class)ss',
        blank=True,
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the work needed.',
    )
    contacts_not_to_approach = models.TextField(
        blank=True,
        help_text='Specific people or organisations the company does not want DIT to talk to.',
    )
    further_info = models.TextField(
        blank=True,
        help_text='Additional notes and useful information.',
    )
    existing_agents = models.TextField(
        blank=True,
        help_text='Contacts the company already has in the market.',
    )

    delivery_date = models.DateField(blank=True, null=True)

    quote = models.OneToOneField(
        Quote,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    invoice = models.OneToOneField(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    po_number = models.CharField(max_length=100, blank=True)

    hourly_rate = models.ForeignKey(
        HourlyRate,
        related_name='%(class)ss',
        on_delete=models.PROTECT,
        default=DEFAULT_HOURLY_RATE,
    )
    discount_value = models.PositiveIntegerField(default=0)
    discount_label = models.CharField(max_length=100, blank=True)

    vat_status = models.CharField(max_length=100, choices=VATStatus.choices, blank=True)
    vat_number = models.CharField(max_length=100, blank=True)
    vat_verified = models.BooleanField(null=True)

    net_cost = models.PositiveIntegerField(
        default=0,
        help_text='Total hours * hourly rate in pence.',
    )
    subtotal_cost = models.PositiveIntegerField(
        default=0,
        help_text='Net cost - discount value in pence.',
    )
    vat_cost = models.PositiveIntegerField(
        default=0,
        help_text='VAT amount of subtotal in pence.',
    )
    total_cost = models.PositiveIntegerField(
        default=0,
        help_text='Subtotal + VAT cost in pence.',
    )

    billing_company_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    billing_address_postcode = models.CharField(max_length=100, blank=True)
    billing_address_country = models.ForeignKey(
        Country,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    paid_on = models.DateTimeField(null=True, blank=True)

    completed_on = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    cancelled_on = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    cancellation_reason = models.ForeignKey(
        CancellationReason,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    # legacy fields, only meant to be used in readonly mode as reference
    product_info = models.TextField(
        blank=True,
        editable=False,
        help_text='Legacy field. What is the product?',
    )
    permission_to_approach_contacts = models.TextField(
        blank=True,
        editable=False,
        help_text='Legacy field. Can DIT speak to the contacts?',
    )
    archived_documents_url_path = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        editable=False,
        help_text='Legacy field. Link to the archived documents for this order.',
    )
    billing_contact_name = models.CharField(
        max_length=MAX_LENGTH,
        blank=True,
        editable=False,
        help_text='Legacy field. Billing contact name.',
    )
    billing_email = models.EmailField(
        max_length=MAX_LENGTH,
        blank=True,
        editable=False,
        help_text='Legacy field. Billing email address.',
    )
    billing_phone = models.CharField(
        max_length=150,
        blank=True,
        editable=False,
        help_text='Legacy field. Billing phone number.',
    )
    contact_email = models.EmailField(
        blank=True,
        editable=False,
        help_text='Legacy field. Contact email specified for this order.',
    )
    contact_phone = models.CharField(
        max_length=254,
        blank=True,
        editable=False,
        help_text='Legacy field. Contact phone number specified for this order.',
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        permissions = (('export_order', 'Can export order'),)
        indexes = [
            # For activity stream
            models.Index(fields=('modified_on', 'id')),
        ]

    def __str__(self):
        """Human-readable representation."""
        return self.reference

    def get_absolute_url(self):
        """URL to the object in the Data Hub internal front end."""
        return get_front_end_url(self)

    def get_current_contact_email(self):
        """:returns: the most up-to-date email address for the contact"""
        return self.contact_email or self.contact.email

    @classmethod
    def generate_reference(cls):
        """:returns: a random unused reference of form:
            <(3) letters><(3) numbers>/<year> e.g. GEA962/16
        :raises RuntimeError: if no reference can be generated
        """

        def gen():
            year_suffix = now().strftime('%y')
            return '{letters}{numbers}/{year}'.format(
                letters=get_random_string(length=3, allowed_chars='ACEFHJKMNPRTUVWXY'),
                numbers=get_random_string(length=3, allowed_chars='123456789'),
                year=year_suffix,
            )

        return generate_reference(model=cls, gen=gen)

    @classmethod
    def generate_public_token(cls):
        """:returns: a random unused public token of form
            <50 uppercase/lowercase letters, digits and symbols>
        :raises RuntimeError: if no public_token can be generated
        """
        gen = partial(secrets.token_urlsafe, 37)
        return generate_reference(model=cls, gen=gen, field='public_token')

    def save(self, *args, **kwargs):
        """Like the django save but it creates a reference and a public token if needed."""
        if not self.reference:
            self.reference = self.generate_reference()
        if not self.public_token:
            self.public_token = self.generate_public_token()

        with transaction.atomic():
            super().save(*args, **kwargs)
            if not self.company_id:
                return
            CompanyActivity.objects.update_or_create(
                order_id=self.id,
                activity_source=CompanyActivity.ActivitySource.order,
                defaults={
                    'date': self.created_on,
                    'company_id': self.company_id,
                },
            )

    def get_lead_assignee(self):
        """:returns: lead OrderAssignee for this order is it exists, None otherwise"""
        return self.assignees.filter(is_lead=True).first()

    def get_datahub_frontend_url(self):
        """Return the url to the Data Hub frontend order page."""
        return f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["order"]}/{self.pk}'

    def get_public_facing_url(self):
        """Return the url to the OMIS public facing order page."""
        return settings.OMIS_PUBLIC_ORDER_URL.format(public_token=self.public_token)

    @transaction.atomic
    def generate_quote(self, by, commit=True):
        """Generate a new quote and assign it to the current order.
        The status of the order changes to "Quote awaiting acceptance".

        :returns: a quote for this order

        :param by: who made the action
        :param commit: if False, the changes will not be saved. Useful for previewing a quote

        :raises rest_framework.exceptions.ValidationError: in case of validation error
        :raises datahub.omis.core.exceptions.Conflict: in case of errors with the state of the
            current order
        :raises RuntimeError: after trying max_retries times without being able to generate a
            valid value for the quote reference
        """
        for validator in [
            validators.OrderDetailsFilledInSubValidator(),
            validators.NoOtherActiveQuoteExistsSubValidator(),
            validators.OrderInStatusSubValidator(
                allowed_statuses=(OrderStatus.DRAFT,),
            ),
        ]:
            validator(order=self)

        self.quote = Quote.objects.create_from_order(order=self, by=by, commit=commit)
        self.status = OrderStatus.QUOTE_AWAITING_ACCEPTANCE
        populate_billing_data(self)

        if commit:
            self.save()

            # send signal
            quote_generated.send(sender=self.__class__, order=self)

        return self.quote

    @transaction.atomic
    def reopen(self, by):
        """Cancel quote and reopen order if possible.
        The status of the order changes back to "Draft".

        :param by: the adviser who is cancelling the quote
        """
        for validator in [
            validators.OrderInStatusSubValidator(
                allowed_statuses=(
                    OrderStatus.QUOTE_AWAITING_ACCEPTANCE,
                    OrderStatus.QUOTE_ACCEPTED,
                ),
            ),
        ]:
            validator(order=self)

        if self.quote:
            self.quote.cancel(by)

        self.status = OrderStatus.DRAFT
        self.save()

        # send signal
        quote_cancelled.send(sender=self.__class__, order=self, by=by)

    def update_invoice_details(self):
        """Generate a new invoice and link it to this order."""
        for validator in [
            validators.OrderInStatusSubValidator(allowed_statuses=(OrderStatus.QUOTE_ACCEPTED,)),
        ]:
            validator(order=self)

        self.invoice = Invoice.objects.create_from_order(self)
        self.save(update_fields=('invoice',))

    @transaction.atomic
    def accept_quote(self, by):
        """Accept quote and change the status of the order to "Quote accepted".

        :param by: the contact who is accepting the quote
        """
        for validator in [
            validators.OrderInStatusSubValidator(
                allowed_statuses=(OrderStatus.QUOTE_AWAITING_ACCEPTANCE,),
            ),
        ]:
            validator(order=self)

        self.quote.accept(by)

        self.status = OrderStatus.QUOTE_ACCEPTED
        self.save()

        # this has to come after saving so that we use the most up-to-date pricing values
        self.update_invoice_details()

        # send signal
        quote_accepted.send(sender=self.__class__, order=self)

    @transaction.atomic
    def mark_as_paid(self, by, payments_data):
        """Mark an order as "Paid".

        :param by: the adviser who created the record
        :param payments_data: list of payments data.
            Each item should at least contain `amount`, `received_on` and `method`
            e.g. [
                {
                    'amount': 1000,
                    'method': 'bacs',
                    'received_on': ...
                },
                {
                    'amount': 1001,
                    'method': 'manual',
                    'received_on': ...
                }
            ]
        """
        for order_validator in [
            validators.OrderInStatusSubValidator(
                allowed_statuses=(OrderStatus.QUOTE_ACCEPTED,),
            ),
        ]:
            order_validator(order=self)

        for payment_validator in [ReconcilablePaymentsSubValidator()]:
            payment_validator(payments_data, self)

        for data in payments_data:
            Payment.objects.create_from_order(self, by, data)

        self.status = OrderStatus.PAID
        max_received_on = max(item['received_on'] for item in payments_data)
        self.paid_on = datetime.combine(date=max_received_on, time=time(tzinfo=timezone.utc))
        self.save()

        # send signal
        order_paid.send(sender=self.__class__, order=self)

    @transaction.atomic
    def complete(self, by):
        """Complete an order.

        :param by: the adviser who marked the order as complete
        """
        for order_validator in [
            validators.OrderInStatusSubValidator(
                allowed_statuses=(OrderStatus.PAID,),
            ),
        ]:
            order_validator(order=self)

        for complete_validator in [validators.CompletableOrderSubValidator()]:
            complete_validator(order=self)

        self.status = OrderStatus.COMPLETE
        self.completed_on = now()
        self.completed_by = by
        self.save()

        # send signal
        order_completed.send(sender=self.__class__, order=self)

    @transaction.atomic
    def cancel(self, by, reason, force=False):
        """Cancel an order.

        :param by: the adviser who cancelled the order
        :param reason: CancellationReason
        :param force: if True, cancelling an order in quote accepted or paid
            is allowed.
        """
        for order_validator in [validators.CancellableOrderSubValidator(force=force)]:
            order_validator(order=self)

        self.status = OrderStatus.CANCELLED
        self.cancelled_on = now()
        self.cancelled_by = by
        self.cancellation_reason = reason
        self.save()

        # send signal
        order_cancelled.send(sender=self.__class__, order=self)


class OrderSubscriber(BaseModel):
    """A subscribed adviser receives notifications when new changes happen to an Order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='subscribers',
    )
    adviser = models.ForeignKey(
        Advisor,
        on_delete=models.CASCADE,
        related_name='+',
    )

    class Meta:
        ordering = ['created_on']
        unique_together = (('order', 'adviser'),)

    def __str__(self):
        """Human-readable representation."""
        return f'{self.order} – {self.adviser}'


class OrderAssignee(BaseModel):
    """An adviser assigned to an Order and responsible for deliverying the final report(s)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='assignees')
    adviser = models.ForeignKey(Advisor, on_delete=models.PROTECT, related_name='+')
    team = models.ForeignKey(Team, blank=True, null=True, on_delete=models.SET_NULL)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)

    estimated_time = models.IntegerField(
        default=0,
        validators=(MinValueValidator(0),),
        help_text='Estimated time in minutes.',
    )
    actual_time = models.IntegerField(
        blank=True,
        null=True,
        validators=(MinValueValidator(0),),
        help_text='Actual time in minutes.',
    )
    is_lead = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_on']
        unique_together = (('order', 'adviser'),)

    def __init__(self, *args, **kwargs):
        """Keep the original adviser value so that we can see if it changes when saving."""
        super().__init__(*args, **kwargs)
        self.__adviser = self.adviser

    def __str__(self):
        """Human-readable representation."""
        return (
            f'{"" if self.is_lead else "Not "}Lead Assignee {self.adviser} for order {self.order}'
        )

    def save(self, *args, **kwargs):
        """Makes sure that the adviser cannot be changed after creation.
        When creating a new instance, it also denormalises `team` and `country` for
        future-proofing reasons, that is, if an adviser moves to another team in the future
        we don't want to change history.
        """
        if not self._state.adding and self.__adviser != self.adviser:
            raise ValueError("Updating the value of adviser isn't allowed.")

        if self._state.adding:
            self.team = self.adviser.dit_team
            if self.team:
                self.country = self.team.country

        super().save(*args, **kwargs)

        self.__adviser = self.adviser
