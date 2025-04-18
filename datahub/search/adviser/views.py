from datahub.search.adviser import AdviserSearchApp
from datahub.search.adviser.serializers import (
    SearchAdviserQuerySerializer,
)
from datahub.search.views import (
    SearchAPIView,
    register_v4_view,
)


class SearchAdviserAPIViewMixin:
    """Defines common settings."""

    search_app = AdviserSearchApp
    serializer_class = SearchAdviserQuerySerializer
    es_sort_by_remappings = {}
    fields_to_exclude = ()

    FILTER_FIELDS = ('id', 'first_name', 'last_name', 'name', 'is_active', 'dit_team')

    REMAP_FIELDS = {'dit_team': 'dit_team.id'}

    COMPOSITE_FILTERS = {
        'first_name': [
            'first_name',  # to find 2-letter words
            'first_name.trigram',
        ],
        'last_name': [
            'last_name',  # to find 2-letter words
            'last_name.trigram',
        ],
    }


@register_v4_view()
class SearchAdviserAPIView(SearchAdviserAPIViewMixin, SearchAPIView):
    pass
