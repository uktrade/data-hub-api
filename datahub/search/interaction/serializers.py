from rest_framework import serializers
from rest_framework.settings import api_settings


class LimitOffsetSerializer(serializers.Serializer):
    """Serialiser used to validate limit/offset values in POST bodies."""

    MAX_RESULTS = 10000

    offset = serializers.IntegerField(default=0, min_value=0, max_value=MAX_RESULTS - 1)
    limit = serializers.IntegerField(default=api_settings.PAGE_SIZE, min_value=1)


class SearchSerializer(LimitOffsetSerializer):
    """Serialiser used to validate interaction search POST bodies."""

    SORT_BY_FIELDS = (
        'company.name',
        'contact.name',
        'date',
        'dit_adviser.name',
        'dit_team.name',
        'id',
        'subject',
    )

    SORT_DIRECTIONS = (
        'asc',
        'desc'
    )

    original_query = serializers.CharField(default='', allow_blank=True)
    sortby = serializers.CharField(default=None)

    def validate_sortby(self, val):
        """
        Validates the sortby field.

        Called by DRF.
        """
        if val is None:
            return None

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
