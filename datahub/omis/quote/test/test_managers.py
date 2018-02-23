from unittest import mock

import pytest
from dateutil.parser import parse as dateutil_parse

from datahub.company.test.factories import AdviserFactory
from ..models import Quote, TermsAndConditions


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestQuoteManager:
    """Tests for the Quote Manager."""

    @mock.patch('datahub.omis.quote.managers.calculate_quote_expiry_date')
    @mock.patch('datahub.omis.quote.managers.generate_quote_reference')
    @mock.patch('datahub.omis.quote.managers.generate_quote_content')
    def test_create_from_order_commit_true(
        self,
        mocked_generate_quote_content,
        mocked_generate_quote_reference,
        mocked_calculate_quote_expiry_date
    ):
        """
        Test that Quote.objects.create_from_order creates a quote
        and commits the changes.
        """
        expiry_date = dateutil_parse('2030-01-01').date()

        mocked_generate_quote_content.return_value = 'Quote content'
        mocked_generate_quote_reference.return_value = 'ABC123'
        mocked_calculate_quote_expiry_date.return_value = expiry_date

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
        assert quote.expires_on == expiry_date
        assert quote.terms_and_conditions == TermsAndConditions.objects.first()

    @mock.patch('datahub.omis.quote.managers.calculate_quote_expiry_date')
    @mock.patch('datahub.omis.quote.managers.generate_quote_reference')
    @mock.patch('datahub.omis.quote.managers.generate_quote_content')
    def test_create_from_order_commit_false(
        self,
        mocked_generate_quote_content,
        mocked_generate_quote_reference,
        mocked_calculate_quote_expiry_date
    ):
        """
        Test that Quote.objects.create_from_order with commit=False builds a quote
        but doesn't commit the changes.
        """
        expiry_date = dateutil_parse('2030-01-01').date()

        mocked_generate_quote_content.return_value = 'Quote content'
        mocked_generate_quote_reference.return_value = 'ABC123'
        mocked_calculate_quote_expiry_date.return_value = expiry_date

        quote = Quote.objects.create_from_order(
            order=mock.MagicMock(),
            by=AdviserFactory(),
            commit=False
        )

        assert quote.reference == 'ABC123'
        assert quote.content == 'Quote content'
        assert not quote.created_by
        assert quote.expires_on == expiry_date
        assert quote.terms_and_conditions == TermsAndConditions.objects.first()

        with pytest.raises(Quote.DoesNotExist):
            quote.refresh_from_db()
