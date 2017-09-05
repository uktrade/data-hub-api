from pathlib import PurePath
from unittest import mock
import pytest
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Country
from datahub.omis.order.test.factories import CancelledQuoteFactory, OrderFactory

from .factories import QuoteFactory
from ..models import Quote

COMPILED_QUOTE_TEMPLATE = PurePath(__file__).parent / 'support/compiled_content.md'


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestGenerateReference:
    """Tests for the generate_reference logic."""

    @mock.patch('datahub.omis.quote.models.get_random_string')
    def test_reference(self, get_random_string):
        """Test that the quote reference is generated as expected."""
        get_random_string.side_effect = ['DE', 4]

        order = mock.Mock(
            reference='ABC123'
        )

        reference = Quote.generate_reference(order)
        assert reference == 'ABC123/Q-DE4'


class TestGenerateContent:
    """Tests for the generate_content logic."""

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
    def test_content(self):
        """Test that the quote content is populated as expected."""
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
        )

        content = Quote.generate_content(order)
        with open(COMPILED_QUOTE_TEMPLATE, 'r') as f:
            expected_content = f.read()

        assert content == expected_content


class TestCancelQuote:
    """Tests for cancelling a quote."""

    def test_cancel_open_quote(self):
        """Test that an open quote can be cancelled."""
        quote = QuoteFactory()
        assert not quote.cancelled_on
        assert not quote.cancelled_by

        adviser = AdviserFactory()

        with freeze_time('2017-07-12 13:00') as mocked_now:
            quote.cancel(by=adviser)

            quote.refresh_from_db()
            assert quote.cancelled_on == mocked_now()
            assert quote.cancelled_by == adviser

    def test_cancel_already_cancelled_quote(self):
        """
        Test that if a quote is already cancelled and you try to cancel it again,
        nothing happens.
        """
        quote = CancelledQuoteFactory()
        assert quote.cancelled_on
        assert quote.cancelled_by
        orig_cancelled_on = quote.cancelled_on
        orig_cancelled_by = quote.cancelled_by

        adviser = AdviserFactory()

        with freeze_time('2017-07-12 13:00') as mocked_now:
            quote.cancel(by=adviser)

            quote.refresh_from_db()
            assert quote.cancelled_on != mocked_now()
            assert quote.cancelled_by != adviser

            assert quote.cancelled_on == orig_cancelled_on
            assert quote.cancelled_by == orig_cancelled_by

    def test_is_cancelled(self):
        """Test when is_cancelled == True."""
        quote = Quote(cancelled_on=now())
        assert quote.is_cancelled()

    def test_is_not_cancelled(self):
        """Test when is_cancelled == False."""
        quote = Quote(cancelled_on=None)
        assert not quote.is_cancelled()
