from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

from datahub.oauth.scopes import Scope
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.export_country_history.serializers import SearchExportCountryHistorySerializer
from datahub.search.interaction.models import Interaction
from datahub.search.permissions import SearchPermissions
from datahub.search.views import register_v4_view, SearchAPIView


@register_v4_view()
class ExportCountryHistoryView(SearchAPIView):
    """Export country history search view."""

    required_scopes = (Scope.internal_front_end,)
    search_app = ExportCountryHistoryApp

    permission_classes = (IsAuthenticatedOrTokenHasScope, SearchPermissions)
    FILTER_FIELDS = [
        'country',
        'company',
    ]

    REMAP_FIELDS = {
        'company': 'company.id',
        'country': 'country.id',
    }

    serializer_class = SearchExportCountryHistorySerializer

    def get_entities(self):
        return [self.search_app.es_model, Interaction]