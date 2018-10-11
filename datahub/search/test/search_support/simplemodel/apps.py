from datahub.search.apps import SearchApp
from datahub.search.test.search_support.models import SimpleModel as DBSimpleModel
from datahub.search.test.search_support.simplemodel.models import ESSimpleModel
from datahub.search.test.search_support.simplemodel.views import (
    SearchSimpleModelAPIView,
    SearchSimpleModelExportAPIView,
)


class SimpleModelSearchApp(SearchApp):
    """SearchApp for SimpleModel."""

    name = 'simplemodel'
    view = SearchSimpleModelAPIView
    export_view = SearchSimpleModelExportAPIView
    es_model = ESSimpleModel
    queryset = DBSimpleModel.objects
    view_permissions = ['search_support.view_simplemodel']
    export_permission = 'search_support.view_simplemodel'
