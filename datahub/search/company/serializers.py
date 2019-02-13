import logging

from rest_framework import serializers

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


logger = logging.getLogger(__name__)


class SearchCompanyQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate company search POST bodies."""

    archived = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    export_to_country = SingleOrListField(child=StringUUIDField(), required=False)
    future_interest_country = SingleOrListField(child=StringUUIDField(), required=False)
    global_headquarters = SingleOrListField(child=StringUUIDField(), required=False)
    headquarter_type = SingleOrListField(
        child=StringUUIDField(allow_null=True),
        required=False,
        allow_null=True,
    )
    name = serializers.CharField(required=False)
    sector = SingleOrListField(child=StringUUIDField(), required=False)
    sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    trading_address_country = SingleOrListField(child=StringUUIDField(), required=False)
    country = SingleOrListField(child=StringUUIDField(), required=False)
    uk_based = serializers.BooleanField(required=False)
    uk_region = SingleOrListField(child=StringUUIDField(), required=False)

    SORT_BY_FIELDS = (
        'archived',
        'archived_by',
        'business_type.name',
        'companies_house_data.company_number',
        'company_number',
        'created_on',
        'employee_range.name',
        'headquarter_type.name',
        'id',
        'modified_on',
        'name',
        'registered_address_town',
        'sector.name',
        'trading_address_town',
        'turnover_range.name',
        'uk_based',
        'uk_region.name',
    )

    # TODO remove following deprecation period.
    deprecated_filters = {
        'description',
        'export_to_country',
        'future_interest_country',
        'global_headquarters',
        'sector',
        'trading_address_country',
    }
    deprecated_sortby_fields = {
        'archived',
        'archived_by',
        'business_type.name',
        'companies_house_data.company_number',
        'company_number',
        'created_on',
        'employee_range.name',
        'headquarter_type.name',
        'id',
        'registered_address_town',
        'sector.name',
        'trading_address_town',
        'turnover_range.name',
        'uk_based',
        'uk_region.name',
    }

    def validate(self, data):
        """
        Logs all deprecated params to make sure we don't break things when we get rid of them.

        TODO Remove following deprecation period.
        """
        deprecated_filters_in_data = data.keys() & self.deprecated_filters
        if deprecated_filters_in_data:
            logger.error(
                'The following deprecated company search filters were '
                f'used: {deprecated_filters_in_data}.',
            )

        sortby = data.get('sortby')
        if sortby and sortby.field in self.deprecated_sortby_fields:
            logger.error(
                'The following deprecated company search sortby field was '
                f'used: {sortby.field}.',
            )
        return super().validate(data)
