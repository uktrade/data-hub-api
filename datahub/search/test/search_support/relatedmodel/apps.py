from datahub.search.apps import SearchApp
from datahub.search.test.search_support.models import RelatedModel as DBRelatedModel
from datahub.search.test.search_support.relatedmodel.models import ESRelatedModel


class RelatedModelSearchApp(SearchApp):
    """SearchApp for RelatedModel."""

    name = 'relatedmodel'
    es_model = ESRelatedModel
    queryset = DBRelatedModel.objects
    view_permissions = ['search_support.view_relatedmodel']
