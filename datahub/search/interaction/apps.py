from datahub.interaction.models import Interaction as DBInteraction, InteractionPermission
from datahub.interaction.permissions import get_allowed_kinds
from datahub.search.apps import SearchApp
from datahub.search.interaction.models import Interaction
from datahub.search.interaction.views import (SearchInteractionAPIView,
                                              SearchInteractionExportAPIView)


class InteractionSearchApp(SearchApp):
    """SearchApp for interactions."""

    name = 'interaction'
    es_model = Interaction
    view = SearchInteractionAPIView
    export_view = SearchInteractionExportAPIView
    permission_required = (f'interaction.{InteractionPermission.read_all}',)
    queryset = DBInteraction.objects.select_related(
        'company',
        'company__sector',
        'company__sector__parent',
        'company__sector__parent__parent',
        'contact',
        'dit_adviser',
        'dit_team',
        'communication_channel',
        'investment_project',
        'investment_project__sector',
        'investment_project__sector__parent',
        'investment_project__sector__parent__parent',
        'service',
        'service_delivery_status',
        'event',
    ).defer(
        # Deferred as policy_area is pending removal
        # TODO: Remove policy_area once policy_areas has been released
        'policy_area',
    )

    def get_permission_filters(self, request):
        """
        Gets permission filter arguments.

        If a user only has permission to access projects associated to their team, this returns
        the filters that should be applied to only return those projects.
        """
        return [('kind', kind) for kind in get_allowed_kinds(request, 'list')]
