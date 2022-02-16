from datahub.search.apps import SearchApp
from datahub.search.test.search_support.models import RelatedModel as DBRelatedModel
from datahub.search.test.search_support.relatedmodel.models import SearchRelatedModel


class RelatedModelSearchApp(SearchApp):
    """SearchApp for RelatedModel."""

    name = 'relatedmodel'
    search_model = SearchRelatedModel
    queryset = DBRelatedModel.objects
    view_permissions = ['search_support.view_relatedmodel']
