from datahub.company.models import Company as DBCompany, CompanyPermission
from datahub.search.apps import SearchApp
from datahub.search.company.models import Company
from datahub.search.company.views import (
    CompanyAutocompleteSearchListAPIView,
    SearchCompanyAPIView,
    SearchCompanyExportAPIView,
)


class CompanySearchApp(SearchApp):
    """SearchApp for company."""

    name = 'company'
    es_model = Company
    view = SearchCompanyAPIView
    export_view = SearchCompanyExportAPIView
    autocomplete_view = CompanyAutocompleteSearchListAPIView
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
        'registered_address_country',
        'sector',
        'sector__parent',
        'sector__parent__parent',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    )
