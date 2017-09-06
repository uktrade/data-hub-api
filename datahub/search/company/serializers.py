from ..serializers import SearchSerializer


class SearchCompanySerializer(SearchSerializer):
    """Serialiser used to validate event search POST bodies."""

    SORT_BY_FIELDS = (
        'account_manager.name',
        'alias',
        'archived',
        'archived_by',
        'business_type.name',
        'classification.name',
        'companies_house_data.company_number',
        'company_number',
        'contacts.name',
        'created_on',
        'employee_range.name',
        'export_to_countries.name',
        'future_interest_countries.name',
        'headquarter_type.name',
        'id',
        'modified_on',
        'name',
        'registered_address_town',
        'sector.name',
        'trading_address_town',
        'turnover_range.name',
        'uk_based',
        'uk_region.name'
    )
