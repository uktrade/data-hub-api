from datahub.search.apps import SearchApp
from datahub.search.test.search_support.models import RelatedModel as DBRelatedModel
from datahub.search.test.search_support.searchappwithsamemodel.models import (
    SearchAppWithSameDBModel,
)


class RelatedModelWithSameDBModelApp(SearchApp):
    """SearchApp which contains the same DB model.
    """

    name = 'related_search_with_same_model'
    search_model = SearchAppWithSameDBModel
    queryset = DBRelatedModel.objects
    view_permissions = [
        'search_support.view_related_search_with_same_model',
    ]
