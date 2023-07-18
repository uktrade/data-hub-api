import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory
from datahub.search.adviser import AdviserSearchApp


pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.opensearch_collector_apps.with_args(AdviserSearchApp),
]


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_adviser_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:adviser')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_advisor_by_id(self, opensearch_with_collector):
        """Tests advisor id search."""
        adviser1 = AdviserFactory()
        AdviserFactory()
        adviser3 = AdviserFactory()

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:adviser')

        response = self.api_client.post(
            url,
            data={
                'id': [adviser1.id, adviser3.id],
            },
        )

        search_results = [adviser['first_name'] for adviser in response.data['results']]
        expected_results = [str(adviser1.first_name), str(adviser3.first_name)]

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert set(search_results) == set(expected_results)

    def test_search_advisor_by_active(self, opensearch_with_collector):
        """Tests advisor id search."""
        active_adviser = AdviserFactory(is_active=True)
        AdviserFactory(is_active=False)

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:adviser')

        response = self.api_client.post(
            url,
            data={
                'is_active': True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(active_adviser.id)
