from opensearch_dsl.query import Term

from datahub.core.permissions import HasPermissions
from datahub.interaction.models import InteractionPermission
from datahub.search.export_country_history import ExportCountryHistoryApp
from datahub.search.export_country_history.serializers import SearchExportCountryHistorySerializer
from datahub.search.interaction.models import Interaction
from datahub.search.views import SearchAPIView, register_v4_view


@register_v4_view()
class ExportCountryHistoryView(SearchAPIView):
    """Export country history search view."""

    search_app = ExportCountryHistoryApp

    permission_classes = (
        # Note: This search view does not use SearchPermissions, as it requires multiple
        # permissions
        HasPermissions(
            'company.view_companyexportcountry',
            f'interaction.{InteractionPermission.view_all}',
        ),
    )

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
        'kind',
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
        """Overriding to provide multiple entities."""
        return [self.search_app.search_model, Interaction]

    def get_base_query(self, request, validated_data):
        """Get the base query.

        This is overridden to exclude UPDATE history items and interactions
        without export countries.
        """
        base_query = super().get_base_query(request, validated_data)

        is_relevant_interaction = Term(were_countries_discussed=True)
        is_relevant_history_entry = Term(_document_type=ExportCountryHistoryApp.name)

        return base_query.filter(is_relevant_interaction | is_relevant_history_entry)
