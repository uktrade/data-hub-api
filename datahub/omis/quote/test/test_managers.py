from unittest import mock
import pytest

from datahub.company.test.factories import AdviserFactory

from ..models import Quote


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestQuoteManager:
    """Tests for the Quote Manager."""

    @mock.patch('datahub.omis.quote.manager.generate_quote_reference')
    @mock.patch('datahub.omis.quote.manager.generate_quote_content')
    def test_create_from_order_commit_true(
        self,
        mocked_generate_quote_content,
        mocked_generate_quote_reference
    ):
        """
        Test that Quote.objects.create_from_order creates a quote
        and commits the changes.
        """
        mocked_generate_quote_content.return_value = 'Quote content'
        mocked_generate_quote_reference.return_value = 'ABC123'

        by = AdviserFactory()
        quote = Quote.objects.create_from_order(
            order=mock.MagicMock(),
            by=by,
            commit=True
        )

        quote.refresh_from_db()
        assert quote.reference == 'ABC123'
        assert quote.content == 'Quote content'
        assert quote.created_by == by

    @mock.patch('datahub.omis.quote.manager.generate_quote_reference')
    @mock.patch('datahub.omis.quote.manager.generate_quote_content')
    def test_create_from_order_commit_false(
        self,
        mocked_generate_quote_content,
        mocked_generate_quote_reference
    ):
        """
        Test that Quote.objects.create_from_order with commit=False builds a quote
        but doesn't commit the changes.
        """
        mocked_generate_quote_content.return_value = 'Quote content'
        mocked_generate_quote_reference.return_value = 'ABC123'

        by = AdviserFactory()
        quote = Quote.objects.create_from_order(
            order=mock.MagicMock(),
            by=by,
            commit=False
        )

        assert quote.reference == 'ABC123'
        assert quote.content == 'Quote content'
        assert quote.created_by == by

        with pytest.raises(Quote.DoesNotExist):
            quote.refresh_from_db()
