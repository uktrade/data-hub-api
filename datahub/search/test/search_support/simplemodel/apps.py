from .models import ESSimpleModel
from .views import SearchSimpleModelAPIView, SearchSimpleModelExportAPIView
from ..models import SimpleModel as DBSimpleModel
from ....apps import SearchApp


class SimpleModelSearchApp(SearchApp):
    """SearchApp for SimpleModel."""

    name = 'simplemodel'
    view = SearchSimpleModelAPIView
    export_view = SearchSimpleModelExportAPIView
    es_model = ESSimpleModel
    queryset = DBSimpleModel.objects
    view_permissions = ['search_support.view_simplemodel']
    export_permission = 'search_support.view_simplemodel'
