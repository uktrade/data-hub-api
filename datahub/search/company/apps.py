from datahub.company.models import Company as DBCompany

from .models import Company
from .views import SearchCompanyAPIView

from ..apps import SearchApp


class CompanySearchApp(SearchApp):
    """SearchApp for company."""

    name = 'company'
    plural_name = 'companies'
    ESModel = Company
    view = SearchCompanyAPIView
    queryset = DBCompany.objects.prefetch_related(
        'account_manager',
        'business_type',
        'classification',
        'employee_range',
        'export_to_countries',
        'future_interest_countries',
        'headquarter_type',
        'one_list_account_owner',
        'registered_address_country',
        'sector',
        'trading_address_country',
        'turnover_range',
    )
