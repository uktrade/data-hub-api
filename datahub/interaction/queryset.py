from datahub.interaction.models import Interaction


def get_interaction_queryset_v3():
    """Gets the interaction query set used by v3 views."""
    return Interaction.objects.select_related(
        'company',
        'contact',
        'dit_adviser',
        'dit_team',
        'communication_channel',
        'investment_project',
        'service',
        'event',
    )
