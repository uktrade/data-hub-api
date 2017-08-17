from datahub.interaction.models import Interaction


def get_interaction_queryset_v1():
    """Gets the interaction query set used by v1 views."""
    return Interaction.objects.select_related(
        'company',
        'contact',
        'dit_adviser',
        'dit_team',
        'interaction_type',
        'service',
        'contact__company',
        'investment_project__investor_company',
    )


def get_interaction_queryset_v3():
    """Gets the interaction query set used by v3 views."""
    return Interaction.objects.select_related(
        'company',
        'contact',
        'dit_adviser',
        'dit_team',
        'interaction_type',
        'service',
    )
