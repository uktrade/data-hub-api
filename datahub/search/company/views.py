from rest_framework.views import APIView

from .models import Company
from ..views import SearchWithFiltersAPIMixin


class SearchCompanyAPIView(SearchWithFiltersAPIMixin, APIView):
    """Filtered company search view."""

    entity = Company

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

    FILTER_FIELDS = (
        'account_manager',
        'export_to_country',
        'future_interest_country',
        'sector',
        'registered_address_country',
        'registered_address_postcode',
        'registered_address_town',
        'trading_address_country',
        'trading_address_postcode',
        'trading_address_town',
        'uk_based',
        'uk_region'
    )

    REMAP_FIELDS = {
        'account_manager': 'account_manager.id',
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'sector': 'sector.id',
        'registered_address_country': 'address_country.id',
        'trading_address_country': 'trading_address_country.id',
        'uk_region': 'uk_region.id',
    }
