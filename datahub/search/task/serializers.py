from rest_framework import serializers


from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchTaskQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate task search POST bodies."""

    id = SingleOrListField(child=StringUUIDField(), required=False)
    # first_name = serializers.CharField(required=False)
    # last_name = serializers.CharField(required=False)
    # name = serializers.CharField(required=False)
    # dit_team = SingleOrListField(
    #     child=StringUUIDField(),
    #     required=False,
    # )
    # is_active = serializers.BooleanField(required=False)
