from datahub.interaction.queryset import get_interaction_queryset_v3

from datahub.search.apps import SearchApp
from datahub.search.interaction.models import Interaction
from datahub.search.interaction.views import SearchInteractionAPIView


class InteractionSearchApp(SearchApp):
    """SearchApp for interactions."""

    name = 'interaction'
    plural_name = 'interactions'
    ESModel = Interaction
    view = SearchInteractionAPIView
    queryset = get_interaction_queryset_v3()
