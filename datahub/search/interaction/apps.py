from datahub.interaction.models import Interaction as DBInteraction
from datahub.search.apps import SearchApp
from datahub.search.interaction.models import Interaction
from datahub.search.interaction.views import (SearchInteractionAPIView,
                                              SearchInteractionExportAPIView)


class InteractionSearchApp(SearchApp):
    """SearchApp for interactions."""

    name = 'interaction'
    ESModel = Interaction
    view = SearchInteractionAPIView
    export_view = SearchInteractionExportAPIView
    permission_required = ('interaction.read_interaction',)
    queryset = DBInteraction.objects.prefetch_related(
        'company',
        'contact',
        'dit_adviser',
        'dit_team',
        'communication_channel',
        'investment_project',
        'service',
        'event',
    )
