from django.db import models

from datahub.omis.core.utils import generate_datetime_based_reference
from datahub.omis.invoice import constants
from datahub.omis.invoice.utils import calculate_payment_due_date


class InvoiceManager(models.Manager):
    """Custom Invoice Manager."""

    def create_from_order(self, order):
        """
        :param order: Order instance for this invoice

        :returns: Invoice object generated from the order
        """
        return self.create(
            order_reference=order.reference,
            invoice_number=generate_datetime_based_reference(self.model, field='invoice_number'),
            payment_due_date=calculate_payment_due_date(order),
            billing_company_name=order.billing_company_name,
            billing_address_1=order.billing_address_1,
            billing_address_2=order.billing_address_2,
            billing_address_town=order.billing_address_town,
            billing_address_county=order.billing_address_county,
            billing_address_postcode=order.billing_address_postcode,
            billing_address_country=order.billing_address_country,
            po_number=order.po_number,
            invoice_company_name=constants.DIT_COMPANY_NAME,
            invoice_address_1=constants.DIT_ADDRESS_1,
            invoice_address_2=constants.DIT_ADDRESS_2,
            invoice_address_town=constants.DIT_ADDRESS_TOWN,
            invoice_address_county=constants.DIT_ADDRESS_COUNTY,
            invoice_address_postcode=constants.DIT_ADDRESS_POSTCODE,
            invoice_address_country_id=constants.DIT_ADDRESS_COUNTRY_ID,
            invoice_vat_number=constants.DIT_VAT_NUMBER,
            contact_email=order.get_current_contact_email(),
            vat_status=order.vat_status,
            vat_number=order.vat_number,
            vat_verified=order.vat_verified,
            net_cost=order.net_cost,
            subtotal_cost=order.subtotal_cost,
            vat_cost=order.vat_cost,
            total_cost=order.total_cost,
        )
