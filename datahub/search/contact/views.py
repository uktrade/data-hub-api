from django.contrib.auth.mixins import PermissionRequiredMixin
from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

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
        'company_name',
        'company_sector',
        'company_uk_region',
        'address_country',
    )

    REMAP_FIELDS = {
        'company_name': 'company.name_trigram',
        'company_sector': 'company_sector.id',
        'company_uk_region': 'company_uk_region.id',
        'address_country': 'address_country.id',
    }


class SearchContactAPIView(SearchContactParams, SearchAPIView, PermissionRequiredMixin):
    """Filtered contact search view."""

    permission_required = 'company.read_contact'
    permission_classes = (IsAuthenticatedOrTokenHasScope,)


class SearchContactExportAPIView(SearchContactParams,
                                 SearchExportAPIView,
                                 PermissionRequiredMixin):
    """Filtered contact search export view."""

    permission_required = 'company.read_contact'
    permission_classes = (IsAuthenticatedOrTokenHasScope,)
