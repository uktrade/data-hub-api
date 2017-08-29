from datahub.company.models import Company as DBCompany

from .models import Company
from .views import SearchCompanyAPIView

from ..apps import SearchApp


class CompanySearchApp(SearchApp):
    """SearchApp for company."""

    name = 'company'
    plural_name = 'companies'
    ESModel = Company
    DBModel = DBCompany
    view = SearchCompanyAPIView
    queryset = DBCompany.objects.prefetch_related(
        'registered_address_country',
        'business_type',
        'sector',
        'employee_range',
        'turnover_range',
        'account_manager',
        'export_to_countries',
        'future_interest_countries',
        'trading_address_country',
        'headquarter_type',
        'classification',
        'one_list_account_owner',
    )
