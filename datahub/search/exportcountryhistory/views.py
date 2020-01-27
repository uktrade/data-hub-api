from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

from datahub.oauth.scopes import Scope
from datahub.search.exportcountryhistory import ExportCountryHistoryApp
from datahub.search.exportcountryhistory.serializers import SearchExportCountryHistorySerializer
from datahub.search.permissions import SearchPermissions
from datahub.search.views import register_v4_view, SearchAPIView


@register_v4_view()
class ExportCountryHistoryView(SearchAPIView):
    """Export country history search view."""

    required_scopes = (Scope.internal_front_end,)
    search_app = ExportCountryHistoryApp

    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchPermissions)
    FILTER_FIELDS = [
        'history_user',
        'country',
        'company',
    ]

    REMAP_FIELDS = {
        'company': 'company.id',
        'country': 'country.id',
    }

    # creates "or" query with a list of fields for given filter name
    # filter must exist in FILTER_FIELDS
    COMPOSITE_FILTERS = {}
    # Remappings from sortby values in the request to the actual field path in the search model
    # e.g. 'name' to 'name.keyword'
    es_sort_by_remappings = {}

    serializer_class = SearchExportCountryHistorySerializer
    fields_to_include = None
    fields_to_exclude = None

    http_method_names = ('post',)
