from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import LeelooTestCase
from .factories import AdvisorFactory


class AdvisorTestCase(LeelooTestCase):
    """Advisor test case."""

    def test_advisor_list_view(self):
        """Should return id and name."""
        AdvisorFactory()
        url = reverse('v1:advisor-list')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
