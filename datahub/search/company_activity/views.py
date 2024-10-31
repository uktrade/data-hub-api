from datahub.dnb_api.utils import (
    get_datahub_ids_for_dnb_service_company_hierarchy,
)
from datahub.search.company_activity import CompanyActivitySearchApp
from datahub.search.company_activity.serializers import (
    SearchCompanyActivityQuerySerializer,
)
from datahub.search.views import (
    register_v4_view,
    SearchAPIView,
)


class SearchCompanyActivityAPIViewMixin:
    """Defines common settings."""

    search_app = CompanyActivitySearchApp
    serializer_class = SearchCompanyActivityQuerySerializer
    es_sort_by_remappings = {}
    fields_to_exclude = ()

    FILTER_FIELDS = (
        'id',
        'date_after',
        'date_before',
        'interaction',
        'company',
        'company_name',
        'activity_source',
        'dit_participants__adviser',
    )

    REMAP_FIELDS = {
        'company': 'company.id',
        'interaction': 'interaction.id',
    }

    COMPOSITE_FILTERS = {
        'company_name': [
            'company.name',  # to find 2-letter words
            'company.name.trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names.trigram',
        ],
        'dit_participants__adviser': [
            'interaction.dit_participants.adviser.id',
            'referral.recipient.id',
            'referral.created_by.id',
        ],
    }


@register_v4_view()
class SearchCompanyActivityAPIView(SearchCompanyActivityAPIViewMixin, SearchAPIView):
    """Filtered company activity search view."""

    def get_base_query(self, request, validated_data):
        """Overwritten to add additional data to the Opensearch query"""
        company_ids = validated_data.get('company')
        if company_ids:
            validated_data = self._include_parent_and_subsidiary_companies(
                validated_data,
                company_ids[0],
            )
        return super().get_base_query(request, validated_data)

    @staticmethod
    def _include_parent_and_subsidiary_companies(validated_data, company_id):
        """Uses dnb-service to get parent and/or subsidiary companies for the given company id."""
        related_company_ids = get_datahub_ids_for_dnb_service_company_hierarchy(
            validated_data.get('include_parent_companies'),
            validated_data.get('include_subsidiary_companies'),
            company_id,
        )

        if related_company_ids['related_companies']:
            validated_data.get('company').extend(related_company_ids['related_companies'])

        return validated_data
