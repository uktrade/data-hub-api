from dateutil.parser import parse as dateutil_parse
from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.search.elasticsearch import MAX_RESULTS


class RelaxedDateTimeField(serializers.Field):
    """
    Relaxed DateTime field.

    Front end uses free text field for data filters, that's why
    we need to accept date/datetime in various different formats.
    DRF DateTimeField doesn't offer that flexibility.
    """

    default_error_messages = {
        'invalid': 'Date is in incorrect format.'
    }

    def to_internal_value(self, data):
        """Parses data into datetime."""
        try:
            data = dateutil_parse(data)
        except ValueError:
            self.fail('invalid', value=data)
        return data


class SingleOrListField(serializers.ListField):
    """Field can be single instance or list."""

    def to_internal_value(self, data):
        """If data is str, creates a list."""
        if isinstance(data, str):
            data = [data]
        return super().to_internal_value(data)


class StringUUIDField(serializers.UUIDField):
    """
    String UUID field.

    We can't use UUID in ES queries, that's why we need to convert them back to string.
    """

    def to_internal_value(self, data):
        """
        Converts string to UUID and then back to string,
        to ensure that string is valid UUID.
        """
        uuid = super().to_internal_value(data)
        return str(uuid)


class NullStringUUIDField(StringUUIDField):
    """
    Null String UUID field.

    We can't use UUID in ES queries, that's why we need to convert them back to string.
    If input value is null-ish, we return None
    """

    NULL_VALUES = {'n', 'N', 'null', 'Null', 'NULL', '', None, 'None'}

    def to_representation(self, value):
        """Converts string to UUID or returns None if null-ish."""
        if value in self.NULL_VALUES:
            return None

        return super().to_representation(value)

    def to_internal_value(self, data):
        """
        Converts string to UUID and then back to string,
        to ensure that string is valid UUID.
        """
        if data in self.NULL_VALUES:
            return None

        return super().to_internal_value(data)


class LimitOffsetSerializer(serializers.Serializer):
    """Serialiser used to validate limit/offset values in POST bodies."""

    offset = serializers.IntegerField(default=0, min_value=0, max_value=MAX_RESULTS - 1)
    limit = serializers.IntegerField(default=api_settings.PAGE_SIZE, min_value=1)


class SearchSerializer(LimitOffsetSerializer):
    """Serialiser used to validate search POST bodies."""

    SORT_BY_FIELDS = []

    SORT_DIRECTIONS = (
        'asc',
        'desc'
    )

    DEFAULT_ORDERING = None

    original_query = serializers.CharField(default='', allow_blank=True)
    sortby = serializers.CharField(default=None)

    def validate_sortby(self, val):
        """
        Validates the sortby field.

        Called by DRF.
        """
        if val is None:
            if self.DEFAULT_ORDERING is None:
                return None
            else:
                val = self.DEFAULT_ORDERING

        errors = []

        field, sep, order = val.partition(':')
        if field not in self.SORT_BY_FIELDS:
            errors.append(f"'sortby' field is not one of {self.SORT_BY_FIELDS}.")

        if sep and order not in self.SORT_DIRECTIONS:
            errors.append(f"Invalid sort direction '{order}', must be one of "
                          f'{self.SORT_DIRECTIONS}')

        if errors:
            raise serializers.ValidationError(errors)

        return val
