from datahub.core.query_utils import get_string_agg_subquery
from datahub.dataset.core.views import BaseDatasetView
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

    def get_dataset(self):
        """Returns list of OMIS Dataset records"""
        return Order.objects.annotate(
            sector_name=get_sector_name_subquery('sector'),
            services=get_string_agg_subquery(Order, 'service_types__name'),
        ).values(
            'cancellation_reason__name',
            'cancelled_on',
            'company__address_1',
            'company__address_2',
            'company__address_town',
            'company__address_county',
            'company__address_country__name',
            'company__address_postcode',
            'company__name',
            'company__registered_address_1',
            'company__registered_address_2',
            'company__registered_address_town',
            'company__registered_address_county',
            'company__registered_address_country__name',
            'company__registered_address_postcode',
            'completed_on',
            'contact__first_name',
            'contact__last_name',
            'contact__telephone_number',
            'contact__email',
            'created_by__dit_team__name',
            'created_on',
            'delivery_date',
            'invoice__subtotal_cost',
            'paid_on',
            'primary_market__name',
            'reference',
            'sector_name',
            'services',
            'status',
            'subtotal_cost',
            'uk_region__name',
        )
