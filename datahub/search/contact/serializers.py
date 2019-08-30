from logging import getLogger

from rest_framework import serializers

from datahub.search.serializers import (
    EntitySearchQuerySerializer,
    SingleOrListField,
    StringUUIDField,
)


logger = getLogger(__name__)


class SearchContactQuerySerializer(EntitySearchQuerySerializer):
    """Serialiser used to validate contact search POST bodies."""

    archived = serializers.BooleanField(required=False)
    name = serializers.CharField(required=False)
    company = SingleOrListField(child=StringUUIDField(), required=False)
    company_name = serializers.CharField(required=False)
    company_sector = SingleOrListField(child=StringUUIDField(), required=False)
    company_sector_descends = SingleOrListField(child=StringUUIDField(), required=False)
    company_uk_region = SingleOrListField(child=StringUUIDField(), required=False)
    address_country = SingleOrListField(child=StringUUIDField(), required=False)
    created_by = SingleOrListField(child=StringUUIDField(), required=False)
    created_on_exists = serializers.BooleanField(required=False)

    # Deprecated sorting options
    # TODO: Remove following deprecation period.
    deprecated_sortby_fields = {
        'accepts_dit_email_marketing',
        'address_county',
        'address_same_as_company',
        'address_town',
        'adviser.name',
        'archived',
        'archived_by.name',
        'archived_on',
        'company_sector.name',
        'email',
        'first_name',
        'id',
        'job_title',
        'name',
        'primary',
        'telephone_countrycode',
        'telephone_number',
        'title.name',
    }

    SORT_BY_FIELDS = (
        'address_country.name',
        'company.name',
        'created_on',
        'last_name',
        'modified_on',
        *deprecated_sortby_fields,
    )

    def validate(self, data):
        """
        Log all uses of deprecated sorting options as an extra check to make sure that they
        aren't being used before we get rid of them.

        TODO: Remove following deprecation period.
        """
        sortby = data.get('sortby')
        if sortby and sortby.field in self.deprecated_sortby_fields:
            logger.error(
                f'The following deprecated contact search sortby field was used: {sortby.field}',
            )
        return super().validate(data)
