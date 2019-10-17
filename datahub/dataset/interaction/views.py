from django.contrib.postgres.aggregates import ArrayAgg

from datahub.core.query_utils import (
    get_aggregate_subquery,
    get_front_end_url_expression,
)
from datahub.dataset.core.views import BaseDatasetView
from datahub.interaction.models import Interaction
from datahub.interaction.queryset import get_base_interaction_queryset
from datahub.metadata.query_utils import get_sector_name_subquery, get_service_name_subquery


class InteractionsDatasetView(BaseDatasetView):
    """
    A GET API view to return all interaction data as required for syncing by
    Data-flow periodically.
    """

    def get_dataset(self):
        """Returns a list of all interaction records"""
        return get_base_interaction_queryset().annotate(
            adviser_ids=get_aggregate_subquery(
                Interaction,
                ArrayAgg('dit_participants__adviser_id', ordering=('dit_participants__id',)),
            ),
            contact_ids=get_aggregate_subquery(
                Interaction,
                ArrayAgg('contacts__id', ordering=('contacts__id',)),
            ),
            interaction_link=get_front_end_url_expression('interaction', 'pk'),
            sector=get_sector_name_subquery('company__sector'),
            service_delivery=get_service_name_subquery('service'),
        ).values(
            'adviser_ids',
            'communication_channel__name',
            'company_id',
            'contact_ids',
            'created_on',
            'date',
            'event_id',
            'grant_amount_offered',
            'interaction_link',
            'investment_project_id',
            'kind',
            'net_company_receipt',
            'notes',
            'sector',
            'service_delivery_status__name',
            'service_delivery',
            'subject',
        )
