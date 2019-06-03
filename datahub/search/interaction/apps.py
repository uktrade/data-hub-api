from django.db.models import Prefetch

from datahub.interaction.models import (
    Interaction as DBInteraction,
    InteractionDITParticipant,
    InteractionPermission,
)
from datahub.search.apps import SearchApp
from datahub.search.interaction.models import Interaction


class InteractionSearchApp(SearchApp):
    """SearchApp for interactions."""

    name = 'interaction'
    es_model = Interaction
    view_permissions = (f'interaction.{InteractionPermission.view_all}',)
    export_permission = f'interaction.{InteractionPermission.export}'
    queryset = DBInteraction.objects.select_related(
        'company',
        'company__sector',
        'company__sector__parent',
        'company__sector__parent__parent',
        'communication_channel',
        'investment_project',
        'investment_project__sector',
        'investment_project__sector__parent',
        'investment_project__sector__parent__parent',
        'service',
        'service_delivery_status',
        'event',
    ).prefetch_related(
        'contacts',
        'policy_areas',
        'policy_issue_types',
        Prefetch(
            'dit_participants',
            queryset=InteractionDITParticipant.objects.select_related('adviser', 'team'),
        ),
    )
