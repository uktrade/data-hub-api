from datahub.company.models import Company as DBCompany
from .models import Company
from .views import SearchCompanyAPIView, SearchCompanyExportAPIView
from ..apps import SearchApp


class CompanySearchApp(SearchApp):
    """SearchApp for company."""

    name = 'company'
    ESModel = Company
    view = SearchCompanyAPIView
    export_view = SearchCompanyExportAPIView
    permission_required = ('company.read_company',)
    queryset = DBCompany.objects.prefetch_related(
        'account_manager',
        'archived_by',
        'business_type',
        'classification',
        'contacts',
        'employee_range',
        'export_experience_category',
        'export_to_countries',
        'future_interest_countries',
        'headquarter_type',
        'one_list_account_owner',
        'parent',
        'global_headquarters',
        'registered_address_country',
        'sector',
        'trading_address_country',
        'turnover_range',
        'uk_region',
    )
