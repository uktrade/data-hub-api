import pytest

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.omis.order.test.factories import OrderFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    with freeze_time('2017-01-01 13:00:00'):
        OrderFactory(reference='ref1')

    with freeze_time('2017-02-01 13:00:00'):
        OrderFactory(reference='ref2')


class TestSearchOrder(APITestMixin):
    """Test specific search for orders."""

    def test_get_all(self, setup_es, setup_data):
        """
        Test that if the querystring is empty and no other params are set,
        it returns all the orders ordered by created_on DESC.
        """
        setup_es.indices.refresh()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2
        assert [
            item['reference'] for item in response.json()['results']
        ] == ['ref2', 'ref1']

    def test_pagination(self, setup_es, setup_data):
        """Tests that the pagination works when speficied as param."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:order')

        # get second page with page size = 1
        response = self.api_client.post(url, {
            'limit': 1,
            'offset': 1,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'ref1'
