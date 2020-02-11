import pytest
from django.db import models
from rest_framework import serializers

from datahub.dbmaintenance.utils import parse_choice


class SampleTextChoice(models.TextChoices):
    """Example text choices."""

    ONE = ('one', 'One')


class SampleIntegerChoice(models.IntegerChoices):
    """Example integer choices."""

    _2 = (2, 'Two')


class TestParseChoiceValue:
    """Tests for parse_choice()."""

    @pytest.mark.parametrize(
        'input_value,choices,expected_value',
        (
            ('one', SampleTextChoice.choices, SampleTextChoice.ONE),
            ('2', SampleIntegerChoice.choices, SampleIntegerChoice._2),
        ),
    )
    def test_accepts_and_transforms_valid_values(self, input_value, choices, expected_value):
        """Test that valid values are accepted and transformed to the internal value."""
        assert parse_choice(input_value, choices) == expected_value

    def test_raises_error_on_invalid_value(self):
        """Test that an error is raised if an invalid value is passed."""
        with pytest.raises(serializers.ValidationError) as excinfo:
            parse_choice('invalid', SampleTextChoice)

        assert excinfo.value.detail == ['"invalid" is not a valid choice.']
