from rest_framework import serializers

from datahub.core.serializers import RelaxedDateField
from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


class SearchCompanyQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate company search POST bodies."""

    id = SingleOrListField(child=StringUUIDField(), required=False)
    archived = serializers.BooleanField(required=False)
    has_name = serializers.BooleanField(required=False)
    headquarter_type = SingleOrListField(
        child=StringUUIDField(allow_null=True),
        required=False,
        allow_null=True,
    )
    name = serializers.CharField(required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    country = SingleOrListField(child=StringUUIDField(), required=False)
    uk_based = serializers.BooleanField(required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    export_to_countries = SingleOrListField(child=StringUUIDField(), required=False)
    future_interest_countries = SingleOrListField(child=StringUUIDField(), required=False)
    one_list_group_global_account_manager = SingleOrListField(
        child=StringUUIDField(),
        required=False,
    )
    adviser = SingleOrListField(child=StringUUIDField(), required=False)
    latest_interaction_date_after = RelaxedDateField(required=False)
    latest_interaction_date_before = RelaxedDateField(required=False)
    uk_postcode = SingleOrListField(child=serializers.CharField(), required=False)
    area = SingleOrListField(child=StringUUIDField(), required=False)
    export_segment = SingleOrListField(required=False)
    export_sub_segment = SingleOrListField(required=False)
    one_list_tier = SingleOrListField(child=StringUUIDField(), required=False)
    duns_number = SingleOrListField(child=serializers.CharField(), required=False)
    number_of_employees = serializers.IntegerField(required=False)
    company_number = SingleOrListField(child=serializers.CharField(), required=False)
    global_ultimate_duns_number = SingleOrListField(child=serializers.CharField(), required=False)
    is_global_ultimate = serializers.BooleanField(required=False)

    SORT_BY_FIELDS = (
        'modified_on',
        'name',
        'latest_interaction_date',
    )

    def to_internal_value(self, data):
        """Convert incoming JSON data to validated data."""
        incoming_data = data.copy()

        # Remove keys with falsy value
        for field in incoming_data.keys():
            if not data[field]:
                data.pop(field)

        # Handle headquarter type checkbox values
        headquarter_type_map = {
            'type_european_hq': 'eb59eaeb-eeb8-4f54-9506-a5e08773046b',
            'type_uk_hq': '3e6debb4-1596-40c5-aa25-f00da0e05af9',
            'type_ultimate_global_hq': '43281c5e-92a4-4794-867b-b4d5f801e6f3',
        }
        headquarter_types = []
        for hq_name, hq_id in headquarter_type_map.items():
            value = data.get(hq_name, None)
            if value:
                headquarter_types.append(hq_id)
        data['headquarter_type'] = headquarter_types

        data.pop('type_european_hq', None)
        data.pop('type_uk_hq', None)
        data.pop('type_ultimate_global_hq', None)

        # Sector
        if 'sector_descends' in data:
            data['sector_descends'] = [data['sector_descends']]

        # Handle status/archived checkbox values
        status_active = data.get('status_active', None)
        status_inactive = data.get('status_inactive', None)

        if status_active and not status_inactive:
            data['archived'] = False
        if not status_active and status_inactive:
            data['archived'] = True

        data.pop('status_active', None)
        data.pop('status_inactive', None)

        # Adviser
        if 'adviser' in data:
            data['adviser'] = [data['adviser']]

        # Country
        if 'country' in data:
            data['country'] = [data['country']]

        return super().to_internal_value(data)


class PublicSearchCompanyQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate public company search POST bodies."""

    archived = serializers.BooleanField(required=False)
    name = serializers.CharField(required=False)
