from datahub.oauth.scopes import Scope
from datahub.search.companieshousecompany.models import CompaniesHouseCompany
from datahub.search.companieshousecompany.serializers import SearchCompaniesHouseCompanySerializer
from datahub.search.views import SearchAPIView


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
