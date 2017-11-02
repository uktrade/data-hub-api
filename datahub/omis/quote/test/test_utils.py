from decimal import Decimal
from pathlib import PurePath
from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.constants import Country
from datahub.omis.order.constants import VATStatus
from datahub.omis.order.test.factories import (
    HourlyRateFactory, OrderAssigneeFactory, OrderFactory
)

from ..utils import (
    calculate_quote_expiry_date,
    generate_quote_content,
    generate_quote_reference
)


COMPILED_QUOTE_TEMPLATE = PurePath(__file__).parent / 'support/compiled_content.md'


@pytest.mark.django_db
class TestGenerateQuoteReference:
    """Tests for the generate_quote_reference logic."""

    @mock.patch('datahub.omis.quote.utils.get_random_string')
    def test_reference(self, get_random_string):
        """Test that the quote reference is generated as expected."""
        get_random_string.side_effect = ['DE', 4]

        order = mock.Mock(
            reference='ABC123'
        )

        reference = generate_quote_reference(order)
        assert reference == 'ABC123/Q-DE4'


@pytest.mark.django_db
class TestGenerateQuoteContent:
    """Tests for the generate_quote_content logic."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_content(self):
        """Test that the quote content is populated as expected."""
        hourly_rate = HourlyRateFactory(rate_value=1250, vat_value=Decimal(17.5))
        company = CompanyFactory(name='My Coorp')
        contact = ContactFactory(
            company=company,
            first_name='John',
            last_name='Doe'
        )
        order = OrderFactory(
            delivery_date=dateutil_parse('2017-06-20'),
            company=company,
            contact=contact,
            reference='ABC123',
            primary_market_id=Country.france.value.id,
            description='lorem ipsum',
            discount_value=100,
            hourly_rate=hourly_rate,
            assignees=[],
            vat_status=VATStatus.uk
        )
        OrderAssigneeFactory(order=order, estimated_time=150)

        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date()
        )
        with open(COMPILED_QUOTE_TEMPLATE, 'r') as f:
            expected_content = f.read()

        assert content == expected_content


class TestCalculateQuoteExpiryDate:
    """Tests for the calculate_quote_expiry_date logic."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_delivery_date_in_far_future(self):
        """
        Now = 18/04/2017
        delivery date = 20/06/2017 (in 2 months)

        Therefore expiry date = 18/05/2017 (in 30 days)
        """
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-06-20').date()
        )
        expiry_date = calculate_quote_expiry_date(order)
        assert expiry_date == dateutil_parse('2017-05-18').date()

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_close_delivery_date(self):
        """
        Now = 18/04/2017
        delivery date = 11/05/2017 (in 23 days)

        Therefore expiry date = 20/04/2017 (in 2 days)
        """
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-05-11').date()
        )
        expiry_date = calculate_quote_expiry_date(order)
        assert expiry_date == dateutil_parse('2017-04-20').date()

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_too_close_delivery_date(self):
        """
        Now = 18/04/2017
        delivery date = 08/05/2017 (in 20 days)

        Therefore expiry date would be passed so an exception is raised.
        """
        order = mock.MagicMock(
            delivery_date=dateutil_parse('2017-05-08').date()
        )

        with pytest.raises(ValidationError):
            calculate_quote_expiry_date(order)
