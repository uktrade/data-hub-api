import uuid

from django.conf import settings
from django.db import models

from datahub.core.models import BaseModel
from datahub.metadata.models import Country

from .managers import InvoiceManager

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Invoice(BaseModel):
    """Details of an invoice."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    invoice_number = models.CharField(max_length=100, unique=True)

    invoice_company_name = models.CharField(max_length=MAX_LENGTH, blank=True)
    invoice_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
    invoice_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
    invoice_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
    invoice_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
    invoice_address_postcode = models.CharField(max_length=100, blank=True)
    invoice_address_country = models.ForeignKey(
        Country,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    invoice_vat_number = models.CharField(max_length=100, blank=True)
    payment_due_date = models.DateField()

    objects = InvoiceManager()

    class Meta:
        permissions = (('read_invoice', 'Can read invoice'),)

    def __str__(self):
        """Human-readable representation"""
        return self.invoice_number
