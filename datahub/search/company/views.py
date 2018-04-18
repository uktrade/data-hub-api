from datahub.oauth.scopes import Scope
from .models import Company
from .serializers import SearchCompanySerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchCompanyParams:
    """Search company parameters."""

    required_scopes = (Scope.internal_front_end,)
    entity = Company
    serializer_class = SearchCompanySerializer

    FILTER_FIELDS = (
        'account_manager',
        'description',
        'export_to_country',
        'future_interest_country',
        'global_headquarters',
        'headquarter_type',
        'name',
        'sector',
        'sector_descends',
        'country',
        'trading_address_country',
        'uk_based',
        'uk_region'
    )

    REMAP_FIELDS = {
        'account_manager': 'account_manager.id',
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'global_headquarters': 'global_headquarters.id',
        'headquarter_type': 'headquarter_type.id',
        'sector': 'sector.id',
        'registered_address_country': 'registered_address_country.id',
        'trading_address_country': 'trading_address_country.id',
        'uk_region': 'uk_region.id',
    }

    COMPOSITE_FILTERS = {
        'name': ['name', 'name_trigram', 'trading_name_trigram'],
        'country': ['trading_address_country.id', 'registered_address_country.id'],
        'sector_descends': ['sector.id', 'sector.ancestors.id'],
    }


class SearchCompanyAPIView(SearchCompanyParams, SearchAPIView):
    """Filtered company search view."""


class SearchCompanyExportAPIView(SearchCompanyParams, SearchExportAPIView):
    """Filtered company search export view."""
