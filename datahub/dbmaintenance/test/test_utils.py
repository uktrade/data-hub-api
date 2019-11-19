import pytest
from model_utils import Choices
from rest_framework import serializers

from datahub.dbmaintenance.utils import parse_choice

CHOICES = Choices(
    ('one', 'One'),
    (2, '_2', 'Two'),
)


class TestParseChoiceValue:
    """Tests for parse_choice()."""

    @pytest.mark.parametrize(
        'input_value,expected_value',
        (
            ('one', CHOICES.one),
            ('2', CHOICES._2),
        ),
    )
    def test_accepts_and_transforms_valid_values(self, input_value, expected_value):
        """Test that valid values are accepted and transformed to the internal value."""
        assert parse_choice(input_value, CHOICES) == expected_value

    def test_raises_error_on_invalid_value(self):
        """Test that an error is raised if an invalid value is passed."""
        with pytest.raises(serializers.ValidationError) as excinfo:
            parse_choice('invalid', CHOICES)

        assert excinfo.value.detail == ['"invalid" is not a valid choice.']
