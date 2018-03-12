from datahub.oauth.scopes import Scope
from .models import Contact
from .serializers import SearchContactSerializer
from ..views import SearchAPIView, SearchExportAPIView


class SearchContactParams:
    """Search contact params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Contact
    serializer_class = SearchContactSerializer

    FILTER_FIELDS = (
        'name',
        'company',
        'company_name',
        'company_sector',
        'company_sector_descends',
        'company_uk_region',
        'created_by',
        'created_on_exists',
        'address_country',
        'archived',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'company_sector': 'company_sector.id',
        'company_uk_region': 'company_uk_region.id',
        'address_country': 'address_country.id',
        'created_by': 'created_by.id',
    }

    COMPOSITE_FILTERS = {
        'name': [
            'name',
            'name_trigram'
        ],
        'company_name': [
            'company.name',
            'company.name_trigram',
            'company.trading_name',
            'company.trading_name_trigram',
        ],
        'company_sector_descends': [
            'company_sector.id',
            'company_sector.ancestors.id',
        ],
    }


class SearchContactAPIView(SearchContactParams, SearchAPIView):
    """Filtered contact search view."""


class SearchContactExportAPIView(SearchContactParams,
                                 SearchExportAPIView):
    """Filtered contact search export view."""
