from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time

from .factories import InvoiceFactory
from ..utils import calculate_payment_due_date, generate_invoice_number


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


class TestCalculatePaymentDueDate:
    """Tests for the calculate_payment_due_date logic."""

    def test_with_delivery_date_in_far_future(self):
        """
        Quote accepted on = 18/04/2017
        delivery date = 20/06/2017 (in 2 months)

        Therefore payment due date = 18/05/2017 (after 30 days)
        """
        quote = mock.MagicMock(
            accepted_on=dateutil_parse('2017-04-18 13:00')
        )
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-06-20').date(),
            quote=quote
        )
        payment_due_date = calculate_payment_due_date(order)
        assert payment_due_date == dateutil_parse('2017-05-18').date()

    def test_with_close_delivery_date(self):
        """
        Quote accepted on = 18/04/2017
        delivery date = 08/05/2017 (in 20 days)

        Therefore payment due date = 24/04/2017 (delivery date - 14 days)
        """
        quote = mock.MagicMock(
            accepted_on=dateutil_parse('2017-04-18 13:00')
        )
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-05-08').date(),
            quote=quote
        )
        payment_due_date = calculate_payment_due_date(order)
        assert payment_due_date == dateutil_parse('2017-04-24').date()
