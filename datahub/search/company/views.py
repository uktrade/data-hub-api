from .models import Company
from .serializers import SearchCompanySerializer
from ..views import SearchAPIView


class SearchCompanyAPIView(SearchAPIView):
    """Filtered company search view."""

    entity = Company
    serializer_class = SearchCompanySerializer

    FILTER_FIELDS = (
        'account_manager',
        'alias',
        'description',
        'export_to_country',
        'future_interest_country',
        'name',
        'sector',
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
