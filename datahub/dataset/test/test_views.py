import pytest
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import (
    format_date_or_datetime,
    get_attr_or_none,
    HawkAPITestClient,
    join_attr_values,
)
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


@pytest.fixture
def hawk_api_client():
    """Hawk API client fixture."""
    yield HawkAPITestClient()


@pytest.fixture
def data_flow_api_client(hawk_api_client):
    """Hawk API client fixture configured to use credentials with the data_flow_api scope."""
    hawk_api_client.set_credentials(
        'data-flow-api-id',
        'data-flow-api-key',
    )
    yield hawk_api_client


@pytest.fixture
def omis_dataset_view_url():
    """Returns OMISDatasetView url"""
    yield reverse('api-v4:dataset:omis-dataset')


def get_expected_data_from_order(order):
    """Returns expected dictionary based on given order"""
    return {
        'delivery_date': str(order.delivery_date),
        'services': join_attr_values(order.service_types.order_by('name')),
        'status': order.status,
        'reference': order.reference,
        'subtotal_cost': order.subtotal_cost,
        'invoice__subtotal_cost': get_attr_or_none(order, 'invoice.subtotal_cost'),
        'company__name': order.company.name,
        'created_by__dit_team__name': order.created_by.dit_team.name,
        'primary_market__name': order.primary_market.name,
        'created_on': (format_date_or_datetime(order.created_on)
                       if order.created_on else None),
        'cancelled_on': (format_date_or_datetime(order.cancelled_on)
                         if order.cancelled_on else None),
        'cancellation_reason__name': get_attr_or_none(order, 'cancellation_reason.name'),
        'uk_region__name': order.uk_region.name,
        'sector__segment': order.sector.segment,
        'paid_on': (format_date_or_datetime(order.paid_on)
                    if order.paid_on else None),
        'completed_on': (format_date_or_datetime(order.completed_on)
                         if order.completed_on else None),
        'contact__first_name': order.contact.first_name,
        'contact__last_name': order.contact.last_name,
        'contact__telephone_number': order.contact.telephone_number,
        'contact__email': order.contact.email,
        'company__address_1': order.company.address_1,
        'company__address_2': order.company.address_2,
        'company__address_town': order.company.address_town,
        'company__address_county': order.company.address_county,
        'company__address_country__name': order.company.address_country.name,
        'company__address_postcode': order.company.address_postcode,
        'company__registered_address_1': order.company.registered_address_1,
        'company__registered_address_2': order.company.registered_address_2,
        'company__registered_address_town': order.company.registered_address_town,
        'company__registered_address_county': order.company.registered_address_county,
        'company__registered_address_country__name': order.company.registered_address_country.name,
        'company__registered_address_postcode': order.company.registered_address_postcode,
    }


@pytest.mark.django_db
class TestOMISDatasetViewSet:
    """
    Tests for OMISDatasetView
    """

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(self, data_flow_api_client, method, omis_dataset_view_url):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, omis_dataset_view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client, omis_dataset_view_url):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client, omis_dataset_view_url):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

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
    def test_success(self, data_flow_api_client, omis_dataset_view_url, order_factory):
        """Test that endpoint returns with expected data for a single order"""
        order = order_factory()
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 1
        result = response_results[0]
        expected_result = get_expected_data_from_order(order)
        assert result == expected_result

    def test_with_multiple_orders(self, data_flow_api_client, omis_dataset_view_url):
        """Test that endpoint returns correct number of record in expected order"""
        with freeze_time('2019-01-01 12:30:00'):
            order_1 = OrderFactory()
        with freeze_time('2019-01-03 12:00:00'):
            order_2 = OrderFactory()
        with freeze_time('2019-01-01 12:00:00'):
            order_3 = OrderFactory()
            order_4 = OrderFactory()

        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        response_results = response.json()['results']
        assert len(response_results) == 4
        expected_order_list = sorted([order_3, order_4],
                                     key=lambda item: item.pk) + [order_1, order_2]
        for index, order in enumerate(expected_order_list):
            assert order.reference == response_results[index]['reference']

    def test_pagination(self, data_flow_api_client, omis_dataset_view_url):
        """Test that when page size higher than threshold response returns with next page url"""
        OrderFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client, omis_dataset_view_url):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
