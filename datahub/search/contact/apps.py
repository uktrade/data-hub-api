from datahub.company.models import Contact as DBContact, ContactPermission
from datahub.search.apps import SearchApp
from datahub.search.contact.models import Contact
from datahub.search.contact.views import SearchContactAPIView, SearchContactExportAPIView


class ContactSearchApp(SearchApp):
    """SearchApp for contacts"""

    name = 'contact'
    es_model = Contact
    view = SearchContactAPIView
    export_view = SearchContactExportAPIView
    view_permissions = (f'company.{ContactPermission.view_contact}',)
    export_permission = f'company.{ContactPermission.export_contact}'
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
