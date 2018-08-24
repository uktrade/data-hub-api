from datahub.oauth.scopes import Scope
from .models import ESSimpleModel
from .serializers import SearchSimpleModelSerializer
from ..models import SimpleModel
from ....views import SearchAPIView, SearchExportAPIView


class SearchSimpleModelParams:
    """Parameters for SimpleModel search views."""

    required_scopes = (Scope.internal_front_end,)
    entity = ESSimpleModel
    serializer_class = SearchSimpleModelSerializer

    FILTER_FIELDS = ('name',)


class SearchSimpleModelAPIView(SearchSimpleModelParams, SearchAPIView):
    """Filtered Simple Model search view."""


class SearchSimpleModelExportAPIView(SearchSimpleModelParams, SearchExportAPIView):
    """Filtered Simple Model search export view."""

    queryset = SimpleModel.objects.all()
    field_titles = {
        'name': 'Name',
    }
