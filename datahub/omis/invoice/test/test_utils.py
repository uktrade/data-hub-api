from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time

from datahub.omis.core.utils import generate_datetime_based_reference
from datahub.omis.order.test.factories import OrderWithAcceptedQuoteFactory
from ..models import Invoice
from ..utils import calculate_payment_due_date


@pytest.mark.django_db
class TestGenerateInvoiceNumber:
    """
    Tests for generating the invoice number using `generate_datetime_based_reference`.

    These are really extra tests just to make sure things work as expected as the main
    logic is been tested by the generic generate_datetime_based_reference tests.
    """

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
                OrderWithAcceptedQuoteFactory()
        assert Invoice.objects.count() == 4

        with freeze_time('2017-02-01 13:00:00'):
            invoice_number = generate_datetime_based_reference(Invoice, field='invoice_number')

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
                OrderWithAcceptedQuoteFactory()
        assert Invoice.objects.count() == 7

        with freeze_time('2017-02-01 13:00:00'):
            invoice_number = generate_datetime_based_reference(Invoice, field='invoice_number')

        assert invoice_number == '201702010004'


class TestCalculatePaymentDueDate:
    """Tests for the calculate_payment_due_date logic."""

    def test_with_delivery_date_in_far_future(self):
        """
        Quote accepted on = 18/04/2017
        delivery date = 20/06/2017 (in 2 months)

        Therefore payment due date = 18/05/2017 (after 30 days)
        """
        quote = mock.MagicMock(
            accepted_on=dateutil_parse('2017-04-18T13:00Z'),
        )
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-06-20').date(),
            quote=quote,
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
            accepted_on=dateutil_parse('2017-04-18T13:00Z'),
        )
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-05-08').date(),
            quote=quote,
        )
        payment_due_date = calculate_payment_due_date(order)
        assert payment_due_date == dateutil_parse('2017-04-24').date()
