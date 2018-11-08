import pytest
from rest_framework import serializers

from datahub.search.serializers import SingleOrListField


class TestSingleOrListField:
    """Tests SingleOrListField."""

    def test_single_value_validation(self):
        """Test that a single value passes validation and is wrapped in a list."""
        field = SingleOrListField(child=serializers.CharField())
        assert field.run_validation('value') == ['value']

    def test_multiple_values_validation(self):
        """Test that list of values passes validation and is returned as a list."""
        field = SingleOrListField(child=serializers.CharField())
        assert field.run_validation(['value1', 'value2']) == ['value1', 'value2']

    def test_single_value_validation_with_error(self):
        """Test that an single invalid value returns an error in the single-item format."""
        field = SingleOrListField(child=serializers.CharField(allow_blank=False))
        with pytest.raises(serializers.ValidationError) as excinfo:
            field.run_validation('')

        assert excinfo.value.get_codes() == ['blank']

    def test_multiple_values_validation_with_error(self):
        """Test that multiple invalid value returns an error for each item."""
        field = SingleOrListField(child=serializers.CharField(allow_blank=False))
        with pytest.raises(serializers.ValidationError) as excinfo:
            field.run_validation(['', ''])

        assert excinfo.value.get_codes() == {0: ['blank'], 1: ['blank']}


class TestSerializerAttributes:
    """Validates the field names specified in class attributes on serialiser classes."""

    def test_sort_by_fields(self, search_app):
        """Validate that the values of SORT_BY_FIELDS are valid field paths."""
        view = search_app.view
        mapping = search_app.es_model._doc_type.mapping

        invalid_fields = {
            field
            for field in view.serializer_class.SORT_BY_FIELDS
            if not mapping.resolve_field(field)
        }

        assert not invalid_fields
