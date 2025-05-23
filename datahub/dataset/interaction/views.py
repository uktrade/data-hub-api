from django.contrib.postgres.aggregates import ArrayAgg

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_array_agg_subquery,
    get_front_end_url_expression,
)
from datahub.dataset.core.views import BaseFilterDatasetView
from datahub.dataset.utils import filter_data_by_modified_date
from datahub.interaction.models import Interaction
from datahub.interaction.queryset import get_base_interaction_queryset
from datahub.metadata.query_utils import get_sector_name_subquery, get_service_name_subquery


class InteractionsDatasetView(BaseFilterDatasetView):
    """A GET API view to return all interaction data as required for syncing by
    Data-flow periodically.
    """

    def get_dataset(self, request):
        """Returns a list of all interaction records."""
        queryset = (
            get_base_interaction_queryset()
            .annotate(
                adviser_ids=get_aggregate_subquery(
                    Interaction,
                    ArrayAgg('dit_participants__adviser_id', order_by=('dit_participants__id',)),
                ),
                contact_ids=get_aggregate_subquery(
                    Interaction,
                    ArrayAgg('contacts__id', order_by=('contacts__id',)),
                ),
                interaction_link=get_front_end_url_expression('interaction', 'pk'),
                policy_area_names=get_array_agg_subquery(
                    Interaction.policy_areas.through,
                    'interaction',
                    'policyarea__name',
                    order_by=('policyarea__order',),
                ),
                related_trade_agreement_names=get_array_agg_subquery(
                    Interaction.related_trade_agreements.through,
                    'interaction',
                    'tradeagreement__name',
                    order_by=('tradeagreement__name',),
                ),
                policy_issue_type_names=get_array_agg_subquery(
                    Interaction.policy_issue_types.through,
                    'interaction',
                    'policyissuetype__name',
                    order_by=('policyissuetype__order',),
                ),
                sector=get_sector_name_subquery('company__sector'),
                service_delivery=get_service_name_subquery('service'),
                export_barrier_type_names=get_array_agg_subquery(
                    Interaction.export_barrier_types.through,
                    'interaction',
                    'exportbarriertype__name',
                    order_by=('exportbarriertype__name',),
                ),
            )
            .values(
                'adviser_ids',
                'communication_channel__name',
                'company_id',
                'contact_ids',
                'created_by_id',
                'created_on',
                'date',
                'event_id',
                'grant_amount_offered',
                'id',
                'interaction_link',
                'investment_project_id',
                'company_export_id',
                'kind',
                'modified_on',
                'net_company_receipt',
                'notes',
                'policy_area_names',
                'policy_feedback_notes',
                'policy_issue_type_names',
                'related_trade_agreement_names',
                'sector',
                'service_delivery_status__name',
                'service_delivery',
                'subject',
                'theme',
                'were_countries_discussed',
                'export_barrier_type_names',
                'export_barrier_notes',
            )
        )
        updated_since = request.GET.get('updated_since')
        filtered_queryset = filter_data_by_modified_date(updated_since, queryset)

        return filtered_queryset
