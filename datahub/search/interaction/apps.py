from datahub.interaction.models import Interaction as DBInteraction
from datahub.interaction.queryset import get_interaction_queryset_v3

from datahub.search.apps import SearchApp
from datahub.search.interaction.models import Interaction
from datahub.search.interaction.views import SearchInteractionAPIView
from datahub.search.models import DataSet


class InteractionSearchApp(SearchApp):
    """SearchApp for interactions."""

    name = 'interaction'
    plural_name = 'interactions'
    ESModel = Interaction
    DBModel = DBInteraction
    view = SearchInteractionAPIView

    def get_dataset(self):
        """Returns dataset that will be synchronised with Elasticsearch."""
        queryset = get_interaction_queryset_v3().order_by('pk')

        return DataSet(queryset, self.ESModel)
