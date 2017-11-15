from decimal import Decimal
from pathlib import PurePath
from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from datahub.company.test.factories import (
    AdviserFactory, CompaniesHouseCompanyFactory,
    CompanyFactory, ContactFactory
)
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
        company = CompanyFactory(
            name='My Coorp',
            registered_address_1='line 1',
            registered_address_2='line 2',
            registered_address_town='London',
            registered_address_county='County',
            registered_address_postcode='SW1A 1AA',
            registered_address_country_id=Country.united_kingdom.value.id
        )
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
            vat_status=VATStatus.uk,
            contact_email='contact-email@mycoorp.com'
        )
        OrderAssigneeFactory(
            order=order,
            adviser=AdviserFactory(
                first_name='Foo',
                last_name='Bar',
            ),
            estimated_time=150,
            is_lead=True
        )

        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date()
        )
        with open(COMPILED_QUOTE_TEMPLATE, 'r') as f:
            expected_content = f.read()

        assert content == expected_content

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_minimal_address(self):
        """
        Test that if the company address doesn't have line2, county and country
        it's formatted correctly.
        """
        company = CompanyFactory(
            registered_address_1='line 1',
            registered_address_2=None,
            registered_address_town='London',
            registered_address_county=None,
            registered_address_postcode='SW1A 1AA',
            registered_address_country_id=None
        )
        order = OrderFactory(
            company=company,
            contact=ContactFactory(company=company)
        )
        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date()
        )

        assert 'line 1, London, SW1A 1AA' in content

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_with_ch_address(self):
        """
        Test that if the company has a companies house record attached,
        its registered address is used instead.
        """
        ch_company = CompaniesHouseCompanyFactory(
            registered_address_1='ch 1',
            registered_address_2='ch 2',
            registered_address_town='Bath',
            registered_address_county='ch county',
            registered_address_postcode='BA1 0AA',
            registered_address_country_id=Country.united_kingdom.value.id
        )
        company = CompanyFactory(
            registered_address_1='line 1',
            registered_address_2='line 2',
            registered_address_town='London',
            registered_address_county='County',
            registered_address_postcode='SW1A 1AA',
            registered_address_country_id=Country.united_kingdom.value.id,
            company_number=ch_company.company_number
        )
        order = OrderFactory(
            company=company,
            contact=ContactFactory(company=company)
        )
        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date()
        )

        assert 'ch 1, ch 2, ch county, Bath, BA1 0AA, United Kingdom' in content

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_pricing_format(self):
        """Test that the pricing is formatted as expected (xx.yy)"""
        hourly_rate = HourlyRateFactory(rate_value=1250, vat_value=Decimal(20))
        order = OrderFactory(
            discount_value=0,
            hourly_rate=hourly_rate,
            assignees=[],
            vat_status=VATStatus.uk
        )
        OrderAssigneeFactory(
            order=order,
            estimated_time=120,
            is_lead=True
        )

        content = generate_quote_content(
            order=order,
            expires_on=dateutil_parse('2017-05-18').date()
        )

        assert '25.00' in content


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
