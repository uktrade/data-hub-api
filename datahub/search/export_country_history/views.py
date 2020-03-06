from elasticsearch_dsl.query import Term
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope

from datahub.company.models import CompanyExportCountryHistory as DBCompanyExportCountryHistory
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

    fields_to_include = (
        # Fields common to interactions and export country history objects
        'company',
        'date',
        'id',

        # Export country history object fields
        'country',
        'history_date',
        'history_type',
        'history_user',
        'status',

        # Interaction fields
        'contacts',
        'dit_participants',
        'export_countries',
        'service',
        'subject',
    )

    FILTER_FIELDS = [
        'country',
        'company',
    ]

    REMAP_FIELDS = {
        'company': 'company.id',
    }

    COMPOSITE_FILTERS = {
        'country': [
            'country.id',
            'export_countries.country.id',
        ],
    }

    serializer_class = SearchExportCountryHistorySerializer

    def get_entities(self):
        """
        Overriding to provide multiple entities
        """
        return [self.search_app.es_model, Interaction]

    def get_base_query(self, request, validated_data):
        """
        Overriding base_query to add extra filters:
        include interactions with export countries:
            - kind: interaction and were_countries_discussed: True
        and export country history items without UPDATEs:
            - history_type: [INSERT, DELETE]
        """
        base_query = super().get_base_query(request, validated_data)
        is_relevant_interaction = Term(were_countries_discussed=True)
        is_relevant_history_entry = (
            Term(history_type=DBCompanyExportCountryHistory.HistoryType.INSERT)
            | Term(history_type=DBCompanyExportCountryHistory.HistoryType.DELETE)
        )

        return base_query.filter(is_relevant_interaction | is_relevant_history_entry)
