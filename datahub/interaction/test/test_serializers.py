from unittest.mock import Mock
from uuid import uuid4

import pytest

from datahub.core.test_utils import MockQuerySet
from datahub.interaction.serializers import _ManyRelatedAsSingleItemField


class TestManyRelatedAsSingleItemField:
    """Tests for _ManyRelatedAsSingleItemField."""

    MOCK_ITEM_1 = Mock(pk=uuid4())
    MOCK_ITEM_2 = Mock(pk=uuid4())

    @pytest.mark.parametrize(
        'value,expected',
        (
            (None, []),
            ({'id': str(MOCK_ITEM_1.pk)}, [MOCK_ITEM_1]),
        )
    )
    def test_to_internal_value(self, value, expected):
        """Test that to_internal_value() returns a list."""
        model = Mock(objects=MockQuerySet([self.MOCK_ITEM_1]))
        field = _ManyRelatedAsSingleItemField(model)
        assert field.to_internal_value(value) == expected

    @pytest.mark.parametrize(
        'value,expected',
        (
            (
                MockQuerySet([]),
                None,
            ),
            (
                MockQuerySet([MOCK_ITEM_1]),
                {'id': str(MOCK_ITEM_1.pk), 'name': MOCK_ITEM_1.name},
            ),
            (
                MockQuerySet([MOCK_ITEM_1, MOCK_ITEM_2]),
                {'id': str(MOCK_ITEM_1.pk), 'name': MOCK_ITEM_1.name},
            ),
        )
    )
    def test_to_representation(self, value, expected):
        """Test that to_representation() returns a single item as a dict."""
        field = _ManyRelatedAsSingleItemField(Mock())
        assert field.to_representation(value) == expected
