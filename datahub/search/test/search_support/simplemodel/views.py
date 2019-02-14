from datahub.oauth.scopes import Scope
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel.models import ESSimpleModel
from datahub.search.test.search_support.simplemodel.serializers import SearchSimpleModelSerializer
from datahub.search.views import SearchAPIView, SearchExportAPIView


class SearchSimpleModelAPIViewMixin:
    """Defines common settings."""

    required_scopes = (Scope.internal_front_end,)
    entity = ESSimpleModel
    serializer_class = SearchSimpleModelSerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    FILTER_FIELDS = ('name',)


class SearchSimpleModelAPIView(SearchSimpleModelAPIViewMixin, SearchAPIView):
    """Filtered Simple Model search view."""


class SearchSimpleModelExportAPIView(SearchSimpleModelAPIViewMixin, SearchExportAPIView):
    """Filtered Simple Model search export view."""

    queryset = SimpleModel.objects.all()
    field_titles = {
        'name': 'Name',
    }
