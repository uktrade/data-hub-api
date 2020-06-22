import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import (
    format_date_or_datetime,
    get_attr_or_none,
    join_attr_values,
)
from datahub.dataset.core.test import BaseDatasetViewTest
from datahub.omis.order.test.factories import (
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
    OrderWithoutAssigneesFactory,
    OrderWithoutLeadAssigneeFactory,
)
from datahub.omis.payment.test.factories import ApprovedRefundFactory


def get_expected_data_from_order(order):
    """Returns expected dictionary based on given order"""
    return {
        'cancellation_reason__name': get_attr_or_none(order, 'cancellation_reason.name'),
        'cancelled_on': format_date_or_datetime(order.cancelled_on),
        'company_id': str(order.company_id),
        'completed_on': format_date_or_datetime(order.completed_on),
        'contact_id': str(order.contact_id),
        'created_by__dit_team_id': str(order.created_by.dit_team_id),
        'created_by_id': str(order.created_by_id) if order.created_by is not None else None,
        'created_on': format_date_or_datetime(order.created_on),
        'delivery_date': format_date_or_datetime(order.delivery_date),
        'id': str(order.id),
        'invoice__subtotal_cost': get_attr_or_none(order, 'invoice.subtotal_cost'),
        'paid_on': format_date_or_datetime(order.paid_on),
        'primary_market__name': get_attr_or_none(order, 'primary_market.name'),
        'quote__accepted_on': format_date_or_datetime(
            get_attr_or_none(order, 'quote.accepted_on'),
        ),
        'quote__created_on': format_date_or_datetime(get_attr_or_none(order, 'quote.created_on')),
        'reference': order.reference,
        'refund_created': (
            format_date_or_datetime(order.refunds.latest('created_on').created_on)
            if order.refunds.exists() else None
        ),
        'refund_total_amount': (
            sum([x.total_amount for x in order.refunds.all()])
            if order.refunds.exists() else None
        ),
        'sector_name': get_attr_or_none(order, 'sector.name'),
        'services': join_attr_values(order.service_types.order_by('name')),
        'status': order.status,
        'subtotal_cost': order.subtotal_cost,
        'total_cost': order.total_cost,
        'uk_region__name': order.uk_region.name,
        'vat_cost': order.vat_cost,
    }


@pytest.mark.django_db
class TestOMISDatasetViewSet(BaseDatasetViewTest):
    """
    Tests for OMISDatasetView
    """

    view_url = reverse('api-v4:dataset:omis-dataset')
    factory = OrderFactory

    @pytest.mark.parametrize(
        'order_factory', (
            OrderFactory,
            OrderCompleteFactory,
            OrderCancelledFactory,
            OrderPaidFactory,
            OrderWithAcceptedQuoteFactory,
            OrderWithCancelledQuoteFactory,
            OrderWithOpenQuoteFactory,
            OrderWithoutAssigneesFactory,
            OrderWithoutLeadAssigneeFactory,
        ))
    def test_success(self, data_flow_api_client, order_factory):
        """Test that endpoint returns with expected data for a single order"""
        order = order_factory()
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_order(order)
        assert result == expected_result

    def test_with_multiple_orders(self, data_flow_api_client):
        """Test that endpoint returns correct number of record in expected order"""
        with freeze_time('2019-01-01 12:30:00'):
            order_1 = OrderFactory()
        with freeze_time('2019-01-03 12:00:00'):
            order_2 = OrderFactory()
        with freeze_time('2019-01-01 12:00:00'):
            order_3 = OrderFactory()
            order_4 = OrderFactory()

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_order_list = sorted([order_3, order_4],
                                     key=lambda item: item.pk) + [order_1, order_2]
        for index, order in enumerate(expected_order_list):
            assert order.reference == response_results[index]['reference']

    @pytest.mark.parametrize(
        'order_factory', (
            OrderFactory,
            OrderCompleteFactory,
            OrderCancelledFactory,
            OrderPaidFactory,
            OrderWithAcceptedQuoteFactory,
            OrderWithCancelledQuoteFactory,
            OrderWithOpenQuoteFactory,
            OrderWithoutAssigneesFactory,
            OrderWithoutLeadAssigneeFactory,
        ))
    def test_order_with_refund(self, data_flow_api_client, order_factory):
        """Test that endpoint returns refund data if it exists"""
        order = order_factory()
        ApprovedRefundFactory(
            order=order,
            requested_amount=order.total_cost / 5,
        )
        ApprovedRefundFactory(
            order=order,
            requested_amount=order.total_cost / 4,
        )
        ApprovedRefundFactory(
            order=order,
            requested_amount=order.total_cost / 3,
        )
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_order(order)
        assert result == expected_result
