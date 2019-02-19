from datahub.oauth.scopes import Scope
from datahub.search.companieshousecompany.models import CompaniesHouseCompany
from datahub.search.serializers import EntitySearchQuerySerializer
from datahub.search.views import SearchAPIView


class SearchCompaniesHouseCompanyAPIViewV3(SearchAPIView):
    """Filtered company search view V3."""

    required_scopes = (Scope.internal_front_end,)
    entity = CompaniesHouseCompany
    serializer_class = EntitySearchQuerySerializer
