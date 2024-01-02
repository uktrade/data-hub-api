from rest_framework import serializers


from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchTaskQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate task search POST bodies."""

    id = SingleOrListField(child=StringUUIDField(), required=False)
    archived = serializers.BooleanField(required=False)
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
    interaction = SingleOrListField(child=StringUUIDField(), required=False)

    SORT_BY_FIELDS = (
        'modified_on',
        'due_date',
        'company.name',
        'investment_project.name',
        'interaction.subject',
    )
