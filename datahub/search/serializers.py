from rest_framework import serializers
from rest_framework.settings import api_settings

from datahub.search.query_builder import MAX_RESULTS


class SingleOrListField(serializers.ListField):
    """Field can be single instance or list."""

    def to_internal_value(self, data):
        """
        If data is str, call the child serialiser's run_validation() directly.

        This is to maintain an error format matching the input (if a list is provided, return an
        error list for each item, otherwise return a single error list).

        (We call self.child.run_validation() rather than self.child.to_internal_value(), because
        ListField performs child field validation in its to_internal_value().)
        """
        if isinstance(data, str):
            return [self.child.run_validation(data)]
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
