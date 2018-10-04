from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory


class TestAdviser(APITestMixin):
    """Adviser test case."""

    def test_adviser_list_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v1:advisor-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_adviser_list_view(self):
        """Should return id and name."""
        AdviserFactory()
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_adviser_filtered_view(self):
        """Test filtering."""
        adviser = AdviserFactory(last_name='UNIQUE')
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(url, data=dict(last_name__icontains='uniq'))
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 1
        result = response_data['results'][0]
        assert result['last_name'] == adviser.last_name
        assert result['telephone_number'] == adviser.telephone_number
        assert result['contact_email'] == adviser.contact_email
        assert result['is_active'] == adviser.is_active

    def test_adviser_list_view_default_sort_order(self):
        """Test default sorting."""
        AdviserFactory(first_name='a', last_name='sorted adviser')
        AdviserFactory(first_name='z', last_name='sorted adviser')
        AdviserFactory(first_name='f', last_name='sorted adviser')
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(
            url,
            data={
                'last_name__icontains': 'sorted',
            },
        )
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result['results']) == 3
        results = result['results']
        assert [res['name'] for res in results] == [
            'a sorted adviser',
            'f sorted adviser',
            'z sorted adviser',
        ]
