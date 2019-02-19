from datahub.company.models import CompaniesHouseCompany as DBCompaniesHouseCompany
from datahub.search.apps import SearchApp
from datahub.search.companieshousecompany.models import CompaniesHouseCompany
from datahub.search.companieshousecompany.views import SearchCompaniesHouseCompanyAPIViewV3


class CompaniesHouseCompanySearchApp(SearchApp):
    """SearchApp for companies house companies."""

    name = 'companieshousecompany'
    es_model = CompaniesHouseCompany
    view = SearchCompaniesHouseCompanyAPIViewV3
    view_permissions = ('company.view_companieshousecompany',)
    queryset = DBCompaniesHouseCompany.objects.select_related(
        'registered_address_country',
    )
    exclude_from_global_search = True
