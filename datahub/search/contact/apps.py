from datahub.company.models import Contact as DBContact
from .models import Contact
from .views import SearchContactAPIView, SearchContactExportAPIView
from ..apps import SearchApp


class ContactSearchApp(SearchApp):
    """SearchApp for contacts"""

    name = 'contact'
    es_model = Contact
    view = SearchContactAPIView
    export_view = SearchContactExportAPIView
    permission_required = ('company.read_contact',)
    queryset = DBContact.objects.select_related(
        'title',
        'company',
        'adviser',
        'address_country',
        'archived_by',
        'company__sector',
        'company__sector__parent',
        'company__sector__parent__parent',
        'company__uk_region',
        'company__registered_address_country',
        'company__trading_address_country',
    )
