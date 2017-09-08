from rest_framework import serializers
from rest_framework.settings import api_settings
from datahub.search.elasticsearch import MAX_RESULTS


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
