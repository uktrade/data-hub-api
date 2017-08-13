from .models import Company
from .views import SearchCompanyAPIView

from ..apps import SearchApp


class CompanySearchApp(SearchApp):
    """SearchApp for company"""

    name = 'company'
    plural_name = 'companies'
    ESModel = Company
    view = SearchCompanyAPIView
