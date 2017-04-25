from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import LeelooTestCase
from datahub.investment.test.factories import InvestmentProjectFactory


class CompanyTestCase(LeelooTestCase):
    """Company test case."""

    def test_list_projects(self):
        """List the companies."""
        project = InvestmentProjectFactory()
        url = reverse('investment:v3:project')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(project.id)
