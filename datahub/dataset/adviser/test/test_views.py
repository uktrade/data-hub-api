from datetime import datetime

import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import format_date_or_datetime, HawkAPITestClient


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


def get_expected_data_from_adviser(adviser):
    """Returns adviser data as a dictionary"""
    return {
        'id': str(adviser.id),
        'date_joined': format_date_or_datetime(adviser.date_joined),
        'first_name': adviser.first_name,
        'last_name': adviser.last_name,
        'telephone_number': adviser.telephone_number,
        'contact_email': adviser.contact_email,
        'dit_team_id': str(adviser.dit_team.id),
        'is_active': adviser.is_active,
    }


@pytest.mark.django_db
class TestAdviserDatasetViewSet:
    """
    Tests for the advisers data-flow export endpoint
    """

    view_url = reverse('api-v4:dataset:advisers-dataset')

    @pytest.mark.parametrize('method', ('delete', 'patch', 'post', 'put'))
    def test_other_methods_not_allowed(
        self,
        data_flow_api_client,
        method,
    ):
        """Test that various HTTP methods are not allowed."""
        response = data_flow_api_client.request(method, self.view_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_without_scope(self, hawk_api_client):
        """Test that making a request without the correct Hawk scope returns an error."""
        hawk_api_client.set_credentials(
            'test-id-without-scope',
            'test-key-without-scope',
        )
        response = hawk_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_without_credentials(self, api_client):
        """Test that making a request without credentials returns an error."""
        response = api_client.get(self.view_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_success(self, data_flow_api_client):
        """Test that endpoint returns with expected data for a single company"""
        adviser = AdviserFactory()
        response = data_flow_api_client.get(self.view_url)

        assert response.status_code == status.HTTP_200_OK

        assert response.json()['results'] == [get_expected_data_from_adviser(adviser)]

    def test_with_multiple_advisers(self, data_flow_api_client):
        """Test that endpoint returns correct order of records"""
        adviser_1 = AdviserFactory(date_joined=datetime(2019, 1, 2))
        adviser_2 = AdviserFactory(date_joined=datetime(2019, 1, 3))
        adviser_3 = AdviserFactory(date_joined=datetime(2019, 1, 1))
        adviser_4 = AdviserFactory(date_joined=datetime(2019, 1, 1))

        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK

        assert [a['id'] for a in response.json()['results']] == [
            str(a.id)
            for a in sorted([adviser_3, adviser_4], key=lambda x: x.id) + [adviser_1, adviser_2]
        ]

    def test_pagination(self, data_flow_api_client):
        """Test that when page size higher than threshold response returns with next page url"""
        AdviserFactory.create_batch(settings.REST_FRAMEWORK['PAGE_SIZE'] + 1)
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['next'] is not None

    def test_no_data(self, data_flow_api_client):
        """Test that without any data available, endpoint completes the request successfully"""
        response = data_flow_api_client.get(self.view_url)
        assert response.status_code == status.HTTP_200_OK
