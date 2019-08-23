import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import format_date_or_datetime, get_attr_or_none, HawkAPITestClient
from datahub.omis.order.test.factories import (
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
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


def omis_dataset_expected_data_generator(order_list, next_page=None, previous_page=None):
    """Generator that returns expected dictionary based on given list of orders"""
    results = []
    for order in order_list:
        results.append({
            'delivery_date': str(order.delivery_date),
            'services': ', '.join((st_name
                                   for st_name
                                   in sorted(order.service_types.values_list('name', flat=True)))),
            'order_status': order.status,
            'omis_order_reference': order.reference,
            'net_price': order.subtotal_cost,
            'subtotal': get_attr_or_none(order, 'invoice.subtotal_cost'),
            'company_name': order.company.name,
            'DIT_team': order.created_by.dit_team.name,
            'market': order.primary_market.name,
            'created_date': (format_date_or_datetime(order.created_on)
                             if order.created_on else None),
            'cancelled_date': (format_date_or_datetime(order.cancelled_on)
                               if order.cancelled_on else None),
            'cancellation_reason_text': get_attr_or_none(order, 'cancellation_reason.name'),
            'UK_region': order.uk_region.name,
            'sector_name': order.sector.segment,
            'payment_received_date': (format_date_or_datetime(order.paid_on)
                                      if order.paid_on else None),
            'completion_date': (format_date_or_datetime(order.completed_on)
                                if order.completed_on else None),
            'contact_first_name': order.contact.first_name,
            'contact_last_name': order.contact.last_name,
            'contact_phone_number': order.contact.telephone_number,
            'contact_email_address': order.contact.email,
            'company_trading_address_line_1': order.company.address_1,
            'company_trading_address_line_2': order.company.address_2,
            'company_trading_address_town': order.company.address_town,
            'company_trading_address_county': order.company.address_county,
            'company_trading_address_country': order.company.address_country.name,
            'company_trading_address_postcode': order.company.address_postcode,
            'company_registered_address_line_1': order.company.registered_address_1,
            'company_registered_address_line_2': order.company.registered_address_2,
            'company_registered_address_town': order.company.registered_address_town,
            'company_registered_address_county': order.company.registered_address_county,
            'company_registered_address_country': order.company.registered_address_country.name,
            'company_registered_address_postcode': order.company.registered_address_postcode,
        })
    return {
        'next': next_page,
        'previous': previous_page,
        'results': results,
    }


@pytest.mark.django_db
class TestOMISDatasetViewSet:
    """
    Tests for OMISDatasetView;
    """

    def test_success(self, data_flow_api_client, omis_dataset_view_url):
        """Test that endpoint returns with expected data for a single order"""
        order = OrderFactory()
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == omis_dataset_expected_data_generator([order])

    def test_with_multiple_orders(self, data_flow_api_client, omis_dataset_view_url):
        """Test that endpoint returns with expected data for multiple orders"""
        order_1 = OrderFactory()
        order_2 = OrderCompleteFactory()
        order_3 = OrderCancelledFactory()
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == omis_dataset_expected_data_generator([order_1, order_2, order_3])

    def test_no_data(self, data_flow_api_client, omis_dataset_view_url):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(omis_dataset_view_url)
        assert response.status_code == status.HTTP_200_OK

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
