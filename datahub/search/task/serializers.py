from rest_framework import serializers


from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchTaskQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate task search POST bodies."""

    id = SingleOrListField(child=StringUUIDField(), required=False)
    title = serializers.CharField(required=False)
    due_date = serializers.DateField(required=False)
    advisers = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    created_by = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    investment_project = SingleOrListField(child=StringUUIDField(), required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
