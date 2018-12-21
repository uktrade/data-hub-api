from datahub.oauth.scopes import Scope
from datahub.search.companieshousecompany.models import CompaniesHouseCompany
from datahub.search.serializers import SearchSerializer
from datahub.search.views import SearchAPIView


class SearchCompaniesHouseCompanyAPIView(SearchAPIView):
    """Filtered company search view."""

    required_scopes = (Scope.internal_front_end,)
    entity = CompaniesHouseCompany
    serializer_class = SearchSerializer
