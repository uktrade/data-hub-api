from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.search.test.search_support.simplemodel.serializers import SearchSimpleModelSerializer
from datahub.search.views import register_v3_view, SearchAPIView, SearchExportAPIView


class SearchSimpleModelAPIViewMixin:
    """Defines common settings."""

    search_app = SimpleModelSearchApp
    serializer_class = SearchSimpleModelSerializer
    es_sort_by_remappings = {
        'name': 'name.keyword',
    }

    FILTER_FIELDS = ('name',)


@register_v3_view()
class SearchSimpleModelAPIView(SearchSimpleModelAPIViewMixin, SearchAPIView):
    """Filtered Simple Model search view."""


@register_v3_view(sub_path='export')
class SearchSimpleModelExportAPIView(SearchSimpleModelAPIViewMixin, SearchExportAPIView):
    """Filtered Simple Model search export view."""

    queryset = SimpleModel.objects.all()
    field_titles = {
        'name': 'Name',
    }
