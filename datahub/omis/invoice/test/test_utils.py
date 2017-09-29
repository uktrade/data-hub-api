import pytest
from freezegun import freeze_time

from .factories import InvoiceFactory
from ..utils import generate_invoice_number


@pytest.mark.django_db
class TestGenerateInvoiceNumber:
    """Tests for the generate_invoice_number logic."""

    def test_first_invoice_number_of_the_day(self):
        """Test that the first invoice number of the day is generated as expected."""
        # create some in different months/days
        dts = (
            '2017-01-01 13:00:00',
            '2017-03-01 13:00:00',
            '2016-02-01 13:00:00',
            '2018-02-01 13:00:00',
        )
        for dt in dts:
            with freeze_time(dt):
                InvoiceFactory()

        with freeze_time('2017-02-01 13:00:00'):
            invoice_number = generate_invoice_number()

        assert invoice_number == '201702010001'

    def test_next_invoice_number_of_the_day(self):
        """Test that the nth invoice number of the day is generated as expected."""
        # create some in different months/days and 3 today
        dts = (
            '2017-01-01 13:00:00',
            '2017-03-01 13:00:00',
            '2016-02-01 13:00:00',
            '2018-02-01 13:00:00',

            '2017-02-01 10:00:00',
            '2017-02-01 11:00:00',
            '2017-02-01 12:00:00',
        )
        for dt in dts:
            with freeze_time(dt):
                InvoiceFactory()

        with freeze_time('2017-02-01 13:00:00'):
            invoice_number = generate_invoice_number()

        assert invoice_number == '201702010004'

    def test_invoice_collision(self):
        """
        Test that if the invoice number has already been used,
        the next available one is generated.
        """
        with freeze_time('2017-01-01 13:00:00'):
            InvoiceFactory(invoice_number='201702010001')
            InvoiceFactory(invoice_number='201702010002')

        with freeze_time('2017-02-01 13:00:00'):
            invoice_number = generate_invoice_number()

        assert invoice_number == '201702010003'
