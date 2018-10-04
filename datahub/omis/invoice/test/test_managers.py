from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.omis.order.test.factories import OrderFactory
from .. import constants
from ..models import Invoice


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestInvoiceManager:
    """Tests for the Invoice Manager."""

    @mock.patch('datahub.omis.invoice.managers.calculate_payment_due_date')
    @mock.patch('datahub.omis.invoice.managers.generate_datetime_based_reference')
    def test_create_from_order(
        self,
        mocked_generate_datetime_based_reference,
        mocked_calculate_payment_due_date,
    ):
        """Test that Invoice.objects.create_from_order creates an invoice."""
        payment_due_date = dateutil_parse('2030-01-01').date()

        mocked_generate_datetime_based_reference.return_value = '201702010004'
        mocked_calculate_payment_due_date.return_value = payment_due_date

        order = OrderFactory()
        invoice = Invoice.objects.create_from_order(order)

        invoice.refresh_from_db()
        assert invoice.order_reference == order.reference
        assert invoice.invoice_number == '201702010004'
        assert invoice.payment_due_date == payment_due_date
        assert invoice.billing_company_name == order.billing_company_name
        assert invoice.billing_address_1 == order.billing_address_1
        assert invoice.billing_address_2 == order.billing_address_2
        assert invoice.billing_address_town == order.billing_address_town
        assert invoice.billing_address_county == order.billing_address_county
        assert invoice.billing_address_postcode == order.billing_address_postcode
        assert invoice.billing_address_country == order.billing_address_country
        assert invoice.po_number == order.po_number
        assert invoice.invoice_company_name == constants.DIT_COMPANY_NAME
        assert invoice.invoice_address_1 == constants.DIT_ADDRESS_1
        assert invoice.invoice_address_2 == constants.DIT_ADDRESS_2
        assert invoice.invoice_address_town == constants.DIT_ADDRESS_TOWN
        assert invoice.invoice_address_county == constants.DIT_ADDRESS_COUNTY
        assert invoice.invoice_address_postcode == constants.DIT_ADDRESS_POSTCODE
        assert str(invoice.invoice_address_country.pk) == constants.DIT_ADDRESS_COUNTRY_ID
        assert invoice.invoice_vat_number == constants.DIT_VAT_NUMBER
        assert invoice.contact_email == order.get_current_contact_email()
        assert invoice.vat_status == order.vat_status
        assert invoice.vat_number == order.vat_number
        assert invoice.vat_verified == order.vat_verified
        assert invoice.net_cost == order.net_cost
        assert invoice.subtotal_cost == order.subtotal_cost
        assert invoice.vat_cost == order.vat_cost
        assert invoice.total_cost == order.total_cost
