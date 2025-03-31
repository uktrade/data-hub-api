from datahub.company.models import Contact as DBContact
from datahub.company.models import ContactPermission
from datahub.search.apps import SearchApp
from datahub.search.contact.models import Contact


class ContactSearchApp(SearchApp):
    """SearchApp for contacts"""

    name = 'contact'
    search_model = Contact
    view_permissions = (f'company.{ContactPermission.view_contact}',)
    export_permission = f'company.{ContactPermission.export_contact}'
    queryset = DBContact.objects.select_related(
        'title',
        'company',
        'adviser',
        'address_area',
        'created_by',
        'created_by__dit_team',
        'address_country',
        'archived_by',
        'company__sector',
        'company__sector__parent',
        'company__sector__parent__parent',
        'company__uk_region',
        'company__address_country',
        'company__registered_address_country',
    )
