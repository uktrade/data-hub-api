from unittest import mock
import pytest

from .. import constants
from ..models import Invoice


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestInvoiceManager:
    """Tests for the Invoice Manager."""

    @mock.patch('datahub.omis.invoice.manager.generate_invoice_number')
    def test_create_populated(self, mocked_generate_invoice_number):
        """Test that Invoice.objects.create_populated creates an invoice."""
        mocked_generate_invoice_number.return_value = '201702010004'

        invoice = Invoice.objects.create_populated()

        invoice.refresh_from_db()
        assert invoice.invoice_number == '201702010004'
        assert invoice.invoice_company_name == constants.DIT_COMPANY_NAME
        assert invoice.invoice_address_1 == constants.DIT_ADDRESS_1
        assert invoice.invoice_address_2 == constants.DIT_ADDRESS_2
        assert invoice.invoice_address_town == constants.DIT_ADDRESS_TOWN
        assert invoice.invoice_address_county == constants.DIT_ADDRESS_COUNTY
        assert invoice.invoice_address_postcode == constants.DIT_ADDRESS_POSTCODE
        assert str(invoice.invoice_address_country.pk) == constants.DIT_ADDRESS_COUNTRY_ID
        assert invoice.invoice_vat_number == constants.DIT_VAT_NUMBER
