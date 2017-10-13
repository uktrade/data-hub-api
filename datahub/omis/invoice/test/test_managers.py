from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse

from .. import constants
from ..models import Invoice


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestInvoiceManager:
    """Tests for the Invoice Manager."""

    @mock.patch('datahub.omis.invoice.manager.calculate_payment_due_date')
    @mock.patch('datahub.omis.invoice.manager.generate_datetime_based_reference')
    def test_create_from_order(
        self,
        mocked_generate_datetime_based_reference,
        mocked_calculate_payment_due_date
    ):
        """Test that Invoice.objects.create_from_order creates an invoice."""
        payment_due_date = dateutil_parse('2030-01-01').date()

        mocked_generate_datetime_based_reference.return_value = '201702010004'
        mocked_calculate_payment_due_date.return_value = payment_due_date

        invoice = Invoice.objects.create_from_order(mock.MagicMock())

        invoice.refresh_from_db()
        assert invoice.invoice_number == '201702010004'
        assert invoice.payment_due_date == payment_due_date
        assert invoice.invoice_company_name == constants.DIT_COMPANY_NAME
        assert invoice.invoice_address_1 == constants.DIT_ADDRESS_1
        assert invoice.invoice_address_2 == constants.DIT_ADDRESS_2
        assert invoice.invoice_address_town == constants.DIT_ADDRESS_TOWN
        assert invoice.invoice_address_county == constants.DIT_ADDRESS_COUNTY
        assert invoice.invoice_address_postcode == constants.DIT_ADDRESS_POSTCODE
        assert str(invoice.invoice_address_country.pk) == constants.DIT_ADDRESS_COUNTRY_ID
        assert invoice.invoice_vat_number == constants.DIT_VAT_NUMBER
