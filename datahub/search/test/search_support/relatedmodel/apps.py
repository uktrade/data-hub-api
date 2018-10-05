from datahub.search.apps import SearchApp
from datahub.search.test.search_support.models import RelatedModel as DBRelatedModel
from datahub.search.test.search_support.relatedmodel.models import ESRelatedModel
from datahub.search.test.search_support.relatedmodel.views import SearchRelatedModelAPIView


class RelatedModelSearchApp(SearchApp):
    """SearchApp for RelatedModel."""

    name = 'relatedmodel'
    view = SearchRelatedModelAPIView
    es_model = ESRelatedModel
    queryset = DBRelatedModel.objects
    view_permissions = []
