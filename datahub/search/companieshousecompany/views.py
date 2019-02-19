from datahub.oauth.scopes import Scope
from datahub.search.companieshousecompany.models import CompaniesHouseCompany
from datahub.search.serializers import EntitySearchQuerySerializer
from datahub.search.views import SearchAPIView


class BaseSearchCompaniesHouseCompanyAPIView(SearchAPIView):
    """Base filtered company search view V3."""

    required_scopes = (Scope.internal_front_end,)
    entity = CompaniesHouseCompany
    serializer_class = EntitySearchQuerySerializer


class SearchCompaniesHouseCompanyAPIViewV3(BaseSearchCompaniesHouseCompanyAPIView):
    """Filtered company search view V3."""

    fields_to_exclude = (
        'registered_address',
    )
