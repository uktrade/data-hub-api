import pytest
from rest_framework.exceptions import ValidationError

from datahub.company_activity.filters import KingsAwardRecipientFilterSet
from datahub.company_activity.models import KingsAwardRecipient
from datahub.company_activity.tests.factories import KingsAwardRecipientFactory

pytestmark = pytest.mark.django_db


class TestKingsAwardRecipientFilterSet:
    """Tests KingsAwardRecipientFilterSet."""

    def test_filter_by_category_alias_single_valid(self):
        """Test filtering by a single valid category alias."""
        innovation_award = KingsAwardRecipientFactory(
            category=KingsAwardRecipient.Category.INNOVATION,
        )
        KingsAwardRecipientFactory(category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE)

        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()
        result = filterset.filter_category(queryset, 'category', 'innovation')

        assert result.count() == 1
        assert result.first() == innovation_award

    def test_filter_by_category_alias_multiple_valid(self):
        """Test filtering by multiple valid category aliases."""
        innovation_award = KingsAwardRecipientFactory(
            category=KingsAwardRecipient.Category.INNOVATION,
        )
        trade_award = KingsAwardRecipientFactory(
            category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
        )
        KingsAwardRecipientFactory(category=KingsAwardRecipient.Category.SUSTAINABLE_DEVELOPMENT)

        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()
        result = filterset.filter_category(queryset, 'category', 'innovation,international-trade')

        assert result.count() == 2
        assert set(result) == {innovation_award, trade_award}

    def test_filter_by_category_alias_mixed_case_and_whitespace(self):
        """Test filtering by category alias with mixed case and whitespace."""
        innovation_award = KingsAwardRecipientFactory(
            category=KingsAwardRecipient.Category.INNOVATION,
        )
        trade_award = KingsAwardRecipientFactory(
            category=KingsAwardRecipient.Category.INTERNATIONAL_TRADE,
        )

        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()
        result = filterset.filter_category(
            queryset,
            'category',
            ' INNOVATION , international-TRADE ',
        )

        assert result.count() == 2
        assert set(result) == {innovation_award, trade_award}

    def test_filter_by_category_alias_single_invalid(self):
        """Test filtering by a single invalid alias raises ValidationError."""
        KingsAwardRecipientFactory()
        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()

        with pytest.raises(ValidationError) as excinfo:
            filterset.filter_category(queryset, 'category', 'invalid-alias')

        assert 'Invalid category alias(es): invalid-alias' in str(excinfo.value)

    def test_filter_by_category_alias_mixed_valid_and_invalid(self):
        """Test filtering by mixed valid and invalid aliases raises ValidationError."""
        KingsAwardRecipientFactory()
        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()

        with pytest.raises(ValidationError) as excinfo:
            filterset.filter_category(queryset, 'category', 'innovation,invalid,trade')

        assert 'Invalid category alias(es): invalid, trade' in str(excinfo.value)

    def test_filter_by_category_alias_all_invalid(self):
        """Test filtering by only invalid aliases raises ValidationError."""
        KingsAwardRecipientFactory()
        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()

        with pytest.raises(ValidationError) as excinfo:
            filterset.filter_category(queryset, 'category', 'invalid1,invalid2')

        assert 'Invalid category alias(es): invalid1, invalid2' in str(excinfo.value)

    def test_filter_by_category_alias_empty_string(self):
        """Test filtering by an empty string returns the original queryset."""
        KingsAwardRecipientFactory.create_batch(3)
        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()
        result = filterset.filter_category(queryset, 'category', '')

        assert result.count() == 3
        assert set(result) == set(queryset)

    def test_filter_by_category_alias_commas_only(self):
        """Test filtering by commas only returns the original queryset."""
        KingsAwardRecipientFactory.create_batch(3)
        queryset = KingsAwardRecipient.objects.all()
        filterset = KingsAwardRecipientFilterSet()
        result = filterset.filter_category(queryset, 'category', ', ,')

        assert result.count() == 3
        assert set(result) == set(queryset)
