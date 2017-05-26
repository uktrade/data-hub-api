from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import LeelooTestCase
from .factories import AdvisorFactory


class AdvisorTestCase(LeelooTestCase):
    """Advisor test case."""

    def test_advisor_list_view(self):
        """Should return id and name."""
        AdvisorFactory()
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_advisor_filtered_view(self):
        """Test filtering."""
        AdvisorFactory(last_name='UNIQUE')
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(url, data=dict(last_name__icontains='uniq'))
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result['results']) == 1
        assert result['results'][0]['last_name'] == 'UNIQUE'
