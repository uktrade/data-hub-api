from datahub.interaction.models import Interaction


def get_interaction_queryset():
    """Gets the interaction query set used by v3 views."""
    return Interaction.objects.select_related(
        'company',
        'contact',
        'dit_adviser',
        'dit_team',
        'communication_channel',
        'investment_project',
        'service',
        'service_delivery_status',
        'event',
        'policy_issue_type',
    ).prefetch_related(
        'policy_areas',
    ).defer(
        # Deferred as policy_area is pending removal
        # TODO: Remove policy_area once policy_areas has been released
        'policy_area',
    )
