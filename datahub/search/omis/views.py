from django.db.models import DecimalField, OuterRef, Subquery, Sum
from django.db.models.functions import Cast

from datahub.core.query_utils import (
    get_choices_as_case_expression,
    get_front_end_url_expression,
    get_full_name_expression,
)
from datahub.metadata.query_utils import get_sector_name_subquery
from datahub.oauth.scopes import Scope
from datahub.omis.order.models import Order as DBOrder
from datahub.omis.order.query_utils import get_lead_order_assignee_name_subquery
from datahub.omis.payment.constants import RefundStatus
from datahub.omis.payment.models import Refund
from datahub.search.omis.models import Order
from datahub.search.omis.serializers import SearchOrderSerializer
from datahub.search.views import SearchAPIView, SearchExportAPIView


class SearchOrderParams:
    """Search order params."""

    required_scopes = (Scope.internal_front_end,)
    entity = Order
    serializer_class = SearchOrderSerializer

    FILTER_FIELDS = [
        'primary_market',
        'sector_descends',
        'uk_region',
        'created_on_before',
        'created_on_after',
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
        'reference': 'reference_trigram',
    }

    COMPOSITE_FILTERS = {
        'contact_name': [
            'contact.name',
            'contact.name_trigram',
        ],
        'company_name': [
            'company.name',
            'company.name_trigram',
            'company.trading_name',
            'company.trading_name_trigram',
            'company.trading_names',  # to find 2-letter words
            'company.trading_names_trigram',
        ],
        'sector_descends': [
            'sector.id',
            'sector.ancestors.id',
        ],
    }


class SearchOrderAPIView(SearchOrderParams, SearchAPIView):
    """Filtered order search view."""


class SearchOrderExportAPIView(SearchOrderParams, SearchExportAPIView):
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
                status=RefundStatus.approved,
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
        'company__registered_address_country__name': 'Company country',
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
