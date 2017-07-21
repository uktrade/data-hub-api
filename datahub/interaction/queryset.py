from datahub.interaction.models import Interaction


def get_interaction_queryset():
    """Gets the interaction query set used by views."""
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
