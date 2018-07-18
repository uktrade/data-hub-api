from .models import ESSimpleModel
from .views import SearchSimpleModelAPIView
from ..models import SimpleModel as DBSimpleModel
from ....apps import SearchApp


class SimpleModelSearchApp(SearchApp):
    """SearchApp for SimpleModel."""

    name = 'simplemodel'
    view = SearchSimpleModelAPIView
    es_model = ESSimpleModel
    queryset = DBSimpleModel.objects
    permission_required = []
