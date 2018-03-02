from rest_framework import serializers

from datahub.core.serializers import NestedRelatedField
from datahub.metadata.models import Country
from .models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    """Invoice DRF serializer."""

    invoice_address_country = NestedRelatedField(Country)
    billing_address_country = NestedRelatedField(Country)

    class Meta:
        model = Invoice
        fields = (
            'created_on',
            'invoice_number',
            'invoice_company_name',
            'invoice_address_1',
            'invoice_address_2',
            'invoice_address_town',
            'invoice_address_county',
            'invoice_address_postcode',
            'invoice_address_country',
            'invoice_vat_number',
            'payment_due_date',
            'billing_contact_name',
            'billing_company_name',
            'billing_address_1',
            'billing_address_2',
            'billing_address_county',
            'billing_address_postcode',
            'billing_address_town',
            'billing_address_country',
            'po_number',
            'vat_status',
            'vat_number',
            'vat_verified',
            'net_cost',
            'subtotal_cost',
            'vat_cost',
            'total_cost',
        )
        read_only_fields = fields
