from ..serializers import SearchSerializer


class SearchContactSerializer(SearchSerializer):
    """Serialiser used to validate event search POST bodies."""

    SORT_BY_FIELDS = (
        'address_country.name',
        'address_county',
        'address_same_as_company',
        'address_town',
        'adviser.name',
        'archived',
        'archived_by.name',
        'company.name',
        'contactable_by_dit',
        'contactable_by_dit_partners',
        'contactable_by_email',
        'contactable_by_phone',
        'created_on',
        'email',
        'first_name',
        'id',
        'job_title',
        'last_name',
        'modified_on',
        'name',
        'primary',
        'telephone_countrycode',
        'telephone_number',
        'title.name',
        'company_sector.name',
    )
