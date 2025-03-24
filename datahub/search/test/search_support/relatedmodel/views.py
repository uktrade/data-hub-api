from datahub.search.test.search_support.relatedmodel import RelatedModelSearchApp
from datahub.search.views import SearchAPIView, register_v3_view


@register_v3_view()
class SearchRelatedModelAPIView(SearchAPIView):
    """RelatedModel search view."""

    search_app = RelatedModelSearchApp
