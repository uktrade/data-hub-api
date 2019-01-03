from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin, get_change_link, ViewOnlyAdmin
from datahub.omis.invoice.models import Invoice
from datahub.omis.order.models import Order


@admin.register(Invoice)
class InvoiceAdmin(BaseModelAdminMixin, ViewOnlyAdmin):
    """View-only admin for invoices."""

    list_display = (
        'invoice_number',
        'order_reference',
        'created_on',
    )
    search_fields = ('order_reference', 'invoice_number')
    fields = (
        'id',
        'created',
        'modified',
        'invoice_number',
        'po_number',
        'order_link',
        'billing_company_name',
        'billing_contact_name',
        'billing_address_1',
        'billing_address_2',
        'billing_address_town',
        'billing_address_county',
        'billing_address_postcode',
        'billing_address_country',
        'invoice_company_name',
        'invoice_address_1',
        'invoice_address_2',
        'invoice_address_town',
        'invoice_address_county',
        'invoice_address_postcode',
        'invoice_address_country',
        'invoice_vat_number',
        'payment_due_date',
        'contact_email',
        'vat_status',
        'vat_number',
        'vat_verified',
        'net_cost',
        'subtotal_cost',
        'vat_cost',
        'total_cost',
    )

    def order_link(self, obj):
        """Returns a link to the order change page."""
        order = Order.objects.filter(reference=obj.order_reference).first()
        if order:
            return get_change_link(order)
        return obj.order_reference

    order_link.short_description = 'order'
