from datahub.oauth.scopes import Scope
from .models import CompaniesHouseCompany
from .serializers import SearchCompaniesHouseCompanySerializer
from ..views import SearchAPIView


class SearchCompaniesHouseCompanyParams:
    """Search company parameters."""

    required_scopes = (Scope.internal_front_end,)
    entity = CompaniesHouseCompany
    serializer_class = SearchCompaniesHouseCompanySerializer

    FILTER_FIELDS = (
        'name',
        'company_number',
        'company_status',
        'incorporation_date_after',
        'incorporation_date_before',
    )

    REMAP_FIELDS = {
        'name': 'name_trigram',
    }


class SearchCompaniesHouseCompanyAPIView(
    SearchCompaniesHouseCompanyParams,
    SearchAPIView,
):
    """Filtered company search view."""
