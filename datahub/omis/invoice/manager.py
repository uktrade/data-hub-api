from django.db import models

from . import constants
from .utils import calculate_payment_due_date, generate_invoice_number


class InvoiceManager(models.Manager):
    """Custom Invoice Manager."""

    def create_from_order(self, order):
        """
        :param order: Order instance for this invoice

        :returns: Invoice object generated from the order
        """
        return self.create(
            invoice_number=generate_invoice_number(),
            payment_due_date=calculate_payment_due_date(order),
            invoice_company_name=constants.DIT_COMPANY_NAME,
            invoice_address_1=constants.DIT_ADDRESS_1,
            invoice_address_2=constants.DIT_ADDRESS_2,
            invoice_address_town=constants.DIT_ADDRESS_TOWN,
            invoice_address_county=constants.DIT_ADDRESS_COUNTY,
            invoice_address_postcode=constants.DIT_ADDRESS_POSTCODE,
            invoice_address_country_id=constants.DIT_ADDRESS_COUNTRY_ID,
            invoice_vat_number=constants.DIT_VAT_NUMBER
        )
