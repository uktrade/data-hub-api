from rest_framework import serializers


from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchAdviserQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate adviser search POST bodies."""

    id = SingleOrListField(child=StringUUIDField(), required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    dit_team = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    is_active = serializers.BooleanField(required=False)
