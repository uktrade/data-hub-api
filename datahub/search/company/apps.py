from datahub.company.models import Company as DBCompany, CompanyPermission
from datahub.search.apps import SearchApp
from datahub.search.company.models import Company
from datahub.search.company.views import (
    CompanyAutocompleteSearchListAPIViewV3,
    CompanyAutocompleteSearchListAPIViewV4,
    SearchCompanyAPIViewV3,
    SearchCompanyAPIViewV4,
    SearchCompanyExportAPIView,
)


class CompanySearchApp(SearchApp):
    """SearchApp for company."""

    name = 'company'
    es_model = Company
    view = SearchCompanyAPIViewV3
    export_view = SearchCompanyExportAPIView
    autocomplete_view = CompanyAutocompleteSearchListAPIViewV3

    view_v4 = SearchCompanyAPIViewV4
    export_view_v4 = SearchCompanyExportAPIView
    autocomplete_view_v4 = CompanyAutocompleteSearchListAPIViewV4

    view_permissions = (f'company.{CompanyPermission.view_company}',)
    export_permission = f'company.{CompanyPermission.export_company}'
    queryset = DBCompany.objects.select_related(
        'archived_by',
        'business_type',
        'employee_range',
        'export_experience_category',
        'headquarter_type',
        'one_list_account_owner',
        'global_headquarters',
        'address_country',
        'registered_address_country',
        'sector',
        'sector__parent',
        'sector__parent__parent',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    ).prefetch_related(
        'export_to_countries',
        'future_interest_countries',
    )
