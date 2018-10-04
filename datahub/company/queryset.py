from datahub.company.models import Contact


def get_contact_queryset():
    """Gets the contact query set used by views."""
    return Contact.objects.select_related(
        'title',
        'company',
        'adviser',
        'address_country',
        'archived_by',
    )
