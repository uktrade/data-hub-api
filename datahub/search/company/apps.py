from datahub.company.models import Company as DBCompany

from .models import Company
from .views import SearchCompanyAPIView

from ..apps import SearchApp
from ..models import DataSet


class CompanySearchApp(SearchApp):
    """SearchApp for company"""

    name = 'company'
    plural_name = 'companies'
    ESModel = Company
    DBModel = DBCompany
    view = SearchCompanyAPIView

    def get_dataset(self):
        """Returns dataset that will be synchronised with Elasticsearch."""
        prefetch_fields = (
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

        qs = self.DBModel.objects.prefetch_related(*prefetch_fields).all().order_by('pk')

        return DataSet(qs, self.ESModel)
