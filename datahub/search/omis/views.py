from django.db.models import DecimalField, OuterRef, Subquery, Sum
from django.db.models.functions import Cast

from datahub.core.query_utils import (
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
)
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.omis.order.models import Order as DBOrder
from datahub.omis.order.query_utils import get_lead_order_assignee_name_subquery
from datahub.omis.payment.constants import RefundStatus
from datahub.omis.payment.models import Refund
from datahub.search.omis import OrderSearchApp
from datahub.search.omis.serializers import SearchOrderQuerySerializer
from datahub.search.views import register_v3_view, SearchAPIView, SearchExportAPIView


class SearchOrderAPIViewMixin:
    """Defines common settings."""

    search_app = OrderSearchApp
    serializer_class = SearchOrderQuerySerializer

    FILTER_FIELDS = [
        'primary_market',
        'sector_descends',
        'uk_region',
        'completed_on_before',
        'completed_on_after',
        'created_on_before',
        'created_on_after',
        'delivery_date_before',
        'delivery_date_after',
        'assigned_to_adviser',
        'assigned_to_team',
        'status',
        'reference',
        'total_cost',
        'subtotal_cost',
        'contact_name',
        'company_name',
        'company',
    ]

    REMAP_FIELDS = {
        'primary_market': 'primary_market.id',
        'uk_region': 'uk_region.id',
        'assigned_to_adviser': 'assignees.id',
        'assigned_to_team': 'assignees.dit_team.id',
        'company': 'company.id',
        'reference': 'reference.trigram',
    }

    COMPOSITE_FILTERS = {
        'contact_name': [
            'contact.name',
            'contact.name.trigram',
        ],
        'company_name': [
            'company.name',
            'company.name.trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names.trigram',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id',
        ],
    }


@register_v3_view()
class SearchOrderAPIView(SearchOrderAPIViewMixin, SearchAPIView):
    """Filtered order search view."""

    subtotal_cost_field = 'subtotal_cost'

    def get_base_query(self, request, validated_data):
        """Enhance entity query with the total subtotal cost."""
        base_query = super().get_base_query(request, validated_data)
        base_query.aggs.bucket(self.subtotal_cost_field, 'sum', field=self.subtotal_cost_field)
        return base_query

    def enhance_response(self, results, response):
        """Enhance response with total subtotal cost."""
        summary = {}

        if self.subtotal_cost_field in results.aggregations:
            total_subtotal_cost = results.aggregations[self.subtotal_cost_field]['value']
            summary[f'total_{self.subtotal_cost_field}'] = total_subtotal_cost

        response['summary'] = summary
        return response


@register_v3_view(sub_path='export')
class SearchOrderExportAPIView(SearchOrderAPIViewMixin, SearchExportAPIView):
    """Order search export view."""

    queryset = DBOrder.objects.annotate(
        subtotal_in_pounds=Cast(
            'subtotal_cost',
            DecimalField(max_digits=19, decimal_places=2),
        ) / 100,
        # This follows the example from
        # https://docs.djangoproject.com/en/2.1/ref/models/expressions/#using-aggregates-within-a-subquery-expression
        net_refund_in_pounds=Subquery(
            Refund.objects.filter(
                order=OuterRef('pk'),
                status=RefundStatus.APPROVED,
            ).order_by(
            ).values(
                'order',
            ).annotate(
                total_refund=Cast(
                    Sum('net_amount'),
                    DecimalField(max_digits=19, decimal_places=2),
                ) / 100,
            ).values(
                'total_refund',
            ),
            output_field=DecimalField(max_digits=19, decimal_places=2),
        ),
        status_name=get_choices_as_case_expression(DBOrder, 'status'),
        link=get_front_end_url_expression('order', 'pk'),
        sector_name=get_sector_name_subquery('sector'),
        company_link=get_front_end_url_expression('company', 'company__pk'),
        contact_name=get_full_name_expression('contact'),
        contact_link=get_front_end_url_expression('contact', 'contact__pk'),
        lead_adviser=get_lead_order_assignee_name_subquery(),
    )
    field_titles = {
        'reference': 'Order reference',
        'subtotal_in_pounds': 'Net price',
        'net_refund_in_pounds': 'Net refund',
        'status_name': 'Status',
        'link': 'Link',
        'sector_name': 'Sector',
        'primary_market__name': 'Market',
        'uk_region__name': 'UK region',
        'company__name': 'Company',
        'company__address_country__name': 'Company country',
        'company__uk_region__name': 'Company UK region',
        'company_link': 'Company link',
        'contact_name': 'Contact',
        'contact__job_title': 'Contact job title',
        'contact_link': 'Contact link',
        'lead_adviser': 'Lead adviser',
        'created_by__dit_team__name': 'Created by team',
        'created_on': 'Date created',
        'delivery_date': 'Delivery date',
        'quote__created_on': 'Date quote sent',
        'quote__accepted_on': 'Date quote accepted',
        'paid_on': 'Date payment received',
        'completed_on': 'Date completed',
    }
