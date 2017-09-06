import pytest
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory
from datahub.omis.order.test.factories import CancelledQuoteFactory

from .factories import QuoteFactory
from ..models import Quote


# mark the whole module for db use
pytestmark = pytest.mark.django_db


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
