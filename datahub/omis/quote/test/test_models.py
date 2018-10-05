import pytest
from django.utils.timezone import now
from freezegun import freeze_time

from datahub.company.test.factories import AdviserFactory, ContactFactory
from datahub.omis.quote.models import Quote
from datahub.omis.quote.test.factories import (
    AcceptedQuoteFactory,
    CancelledQuoteFactory,
    QuoteFactory,
)


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

        with freeze_time('2017-07-12 13:00'):
            quote.cancel(by=adviser)

            quote.refresh_from_db()
            assert quote.cancelled_on == now()
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


class TestAcceptQuote:
    """Tests for accepting a quote."""

    def test_accept_open_quote(self):
        """Test that an open quote can be accepted."""
        quote = QuoteFactory()
        assert not quote.accepted_on
        assert not quote.accepted_by

        contact = ContactFactory()

        with freeze_time('2017-07-12 13:00'):
            quote.accept(by=contact)

            quote.refresh_from_db()
            assert quote.accepted_on == now()
            assert quote.accepted_by == contact

    def test_accept_already_accepted_quote(self):
        """
        Test that if a quote has already been accepted and you try to accept it again,
        nothing happens.
        """
        quote = AcceptedQuoteFactory()
        assert quote.accepted_on
        assert quote.accepted_by
        orig_accepted_on = quote.accepted_on
        orig_accepted_by = quote.accepted_by

        contact = ContactFactory()

        with freeze_time('2017-07-12 13:00') as mocked_now:
            quote.accept(by=contact)

            quote.refresh_from_db()
            assert quote.accepted_on != mocked_now()
            assert quote.accepted_by != contact

            assert quote.accepted_on == orig_accepted_on
            assert quote.accepted_by == orig_accepted_by

    def test_cannot_accept_cancelled_quote(self):
        """Test that if the quote has been cancelled, it cannot be accepted."""
        quote = CancelledQuoteFactory()
        assert quote.cancelled_on
        assert quote.cancelled_by

        contact = ContactFactory()
        with pytest.raises(AssertionError):
            quote.accept(by=contact)

    def test_is_accepted(self):
        """Test when is_accepted == True."""
        quote = Quote(accepted_on=now())
        assert quote.is_accepted()

    def test_is_not_accepted(self):
        """Test when is_accepted == False."""
        quote = Quote(accepted_on=None)
        assert not quote.is_accepted()
