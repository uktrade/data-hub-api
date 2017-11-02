from datahub.core.permissions import UserHasPermissions
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
        'trading_name',
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
        'trading_name': 'trading_name_trigram',
        'account_manager': 'account_manager.id',
        'export_to_country': 'export_to_countries.id',
        'future_interest_country': 'future_interest_countries.id',
        'sector': 'sector.id',
        'registered_address_country': 'address_country.id',
        'trading_address_country': 'trading_address_country.id',
        'uk_region': 'uk_region.id',
    }


class SearchCompanyAPIView(SearchCompanyParams, SearchAPIView):
    """Filtered company search view."""

    permission_classes = SearchAPIView.permission_classes + (UserHasPermissions, )
    permission_required = 'company.read_company'


class SearchCompanyExportAPIView(SearchCompanyParams, SearchExportAPIView):
    """Filtered company search export view."""

    permission_classes = SearchAPIView.permission_classes + (UserHasPermissions,)
    permission_required = 'company.read_company'
