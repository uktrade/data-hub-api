from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError

from datahub.core.fields import MultipleChoiceField


@pytest.fixture()
def field():
    """Instance of MultipleChoiceField with three choices."""
    yield MultipleChoiceField(
        max_length=255,
        choices=(
            ('option1', 'Option 1'),
            ('option2', 'Option 2'),
            ('option3', 'Option 3'),
        )
    )


class TestMultipleChoiceField:
    """Tests MultipleChoiceField."""

    def test_clean(self, field):
        """Test clean() with a valid set of choices."""
        instance = Mock()
        data = ['option1', 'option2', 'option3']
        assert field.clean(data, instance) == data

    def test_clean_rejects_duplicates(self, field):
        """Test clean() with a duplicate choice."""
        instance = Mock()
        with pytest.raises(ValidationError) as excinfo:
            field.clean(['option1', 'option2', 'option1'], instance)
        assert excinfo.value.code == 'item_duplicated'

    def test_clean_rejects_invalid_choices(self, field):
        """Test clean() with an invalid choice."""
        instance = Mock()
        with pytest.raises(ValidationError) as excinfo:
            field.clean(['option3', 'option4'], instance)
        assert excinfo.value.code == 'item_invalid'
