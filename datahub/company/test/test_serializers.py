import pytest

from datahub.company.serializers import _ArrayAsSingleItemField


class TestArrayAsSingleItemField:
    """Tests for _ArrayAsSingleItemField."""

    @pytest.mark.parametrize(
        'value,expected',
        (
            (None, []),
            ('', []),
            ('value', ['value']),
        ),
    )
    def test_run_validation(self, value, expected):
        """Test that run_validation() returns a list."""
        field = _ArrayAsSingleItemField(required=False, allow_null=True, allow_blank=True)
        assert field.run_validation(value) == expected

    @pytest.mark.parametrize(
        'value,expected',
        (
            (
                [],
                '',
            ),
            (
                None,
                '',
            ),
            (
                ['value'],
                'value',
            ),
        ),
    )
    def test_to_representation(self, value, expected):
        """Test that to_representation() returns a single item from the list."""
        field = _ArrayAsSingleItemField()
        assert field.to_representation(value) == expected
