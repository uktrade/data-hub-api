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


class SearchCompaniesHouseCompanyAPIViewV4(BaseSearchCompaniesHouseCompanyAPIView):
    """Filtered company search view V4."""

    fields_to_exclude = (
        'registered_address_1',
        'registered_address_2',
        'registered_address_town',
        'registered_address_county',
        'registered_address_country',
        'registered_address_postcode',
    )
