from rest_framework.reverse import reverse
from rest_framework import status

from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.company.test.factories import CompanyFactory


class TestCompanyActivityViewSetV4(APITestMixin):
    """Tests for the get CompanyActivityViewSetV4."""

    def test_company_activity_endpoint(self):

        requester = create_test_user()
        company = CompanyFactory()

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v4:company-activity:activity', kwargs={'pk': company.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['id'] == str(company.id)
        assert response_data['name'] == company.name
        assert response_data['trading_names'] == company.trading_names
