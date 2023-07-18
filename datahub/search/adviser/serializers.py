from rest_framework import serializers

from datahub.core.serializers import RelaxedDateField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchAdviserQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate adviser search POST bodies."""

    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
