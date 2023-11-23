from django.db.models import CharField, Max, Sum
from django.db.models.functions import Cast

from datahub.core.query_utils import get_aggregate_subquery, get_string_agg_subquery
from datahub.dataset.core.views import BaseDatasetView
from datahub.dbmaintenance.utils import parse_date
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.omis.order.models import Order


class OMISDatasetView(BaseDatasetView):
    """
    An APIView that provides 'get' action which queries and returns desired fields for OMIS Dataset
    to be consumed by Data-flow periodically. Data-flow uses response result to insert data into
    Dataworkspace through its defined API endpoints. The goal is presenting various reports to the
    users out of flattened table and let analyst to work on denormalized table to get
    more meaningful insight.
    """

    def get(self, request):
        """Endpoint which serves all records for Orders Dataset"""
        dataset = self.get_dataset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(dataset, request, view=self)
        self._enrich_data(page)
        return paginator.get_paginated_response(page)

    def get_dataset(self, request):
        """Returns list of OMIS Dataset records"""
        queryset = Order.objects.annotate(
            refund_created=get_aggregate_subquery(Order, Max('refunds__created_on')),
            refund_total_amount=get_aggregate_subquery(Order, Sum('refunds__total_amount')),
            sector_name=get_sector_name_subquery('sector'),
            services=get_string_agg_subquery(Order, Cast('service_types__name', CharField())),
        ).values(
            'cancellation_reason__name',
            'cancelled_on',
            'company_id',
            'completed_on',
            'contact_id',
            'created_by__dit_team_id',
            'created_by_id',
            'created_on',
            'delivery_date',
            'id',
            'invoice__subtotal_cost',
            'paid_on',
            'primary_market__name',
            'quote__accepted_on',
            'quote__created_on',
            'reference',
            'refund_created',
            'refund_total_amount',
            'sector_name',
            'services',
            'status',
            'subtotal_cost',
            'total_cost',
            'uk_region__name',
            'vat_cost',
        )
        updated_since = request.GET.get('updated_since')
        if updated_since:
            updated_since_date = parse_date(updated_since)
            if updated_since_date:
                queryset = queryset.filter(modified_on__gt=updated_since_date)

        return queryset
