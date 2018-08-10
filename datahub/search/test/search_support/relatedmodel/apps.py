from .models import ESRelatedModel
from .views import SearchRelatedModelAPIView
from ..models import RelatedModel as DBRelatedModel
from ....apps import SearchApp


class RelatedModelSearchApp(SearchApp):
    """SearchApp for RelatedModel."""

    name = 'relatedmodel'
    view = SearchRelatedModelAPIView
    es_model = ESRelatedModel
    queryset = DBRelatedModel.objects
    permission_required = []
