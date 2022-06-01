from datahub.event.models import Event


def get_base_event_queryset():
    """
    Gets the base eveb queryset.
    """
    return Event.objects.select_related(
        'created_by',
        'modified_by',
        'event_type',
        'location_type',
        'address_country',
        'uk_region',
        'organiser',
        'lead_team',
        'service'
    )
