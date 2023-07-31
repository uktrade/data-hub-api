from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)


class TestGettingObjectivesForCompany(APITestMixin):
    """Tests to retrieve a single objective for a company."""

    def test_missing_mandatory_fields_return_expected_error(self):
        """
        Test when mandatory fields are not provided these fields are included in the
        error response
        """
        company = CompanyFactory()
        url = reverse('api-v4:objective:list', kwargs={'company_id': company.id})

        response = self.api_client.get(
            url,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ['This field is required.'],
            'owner': ['This field is required.'],
            'contacts': ['This field is required.'],
            'destination_country': ['This field is required.'],
            'sector': ['This field is required.'],
            'estimated_export_value_years': ['This field is required.'],
            'title': ['This field is required.'],
            'estimated_export_value_amount': ['This field is required.'],
            'estimated_win_date': ['This field is required.'],
            'export_potential': ['This field is required.'],
        }

    # def test_company_has_no_objectives(self):
    #     company = CompanyFactory()
    #     url = reverse('api-v4:objective:objective-list', kwargs={'company_id': company.id})
    #     response = self.api_client.get(url)

    #     assert response.status_code == status.HTTP_200_OK
    #     assert response.json()['count'] == 2
    # company = CompanyFactory()
    # user = create_test_user(
    #     permission_codenames=(
    #         'view_company',
    #         'view_company_document',
    #     ),
    # )
    # api_client = self.create_api_client(user=user)
    # print('******', api_client)
    # url = reverse('api-v4:objective:objective-list', kwargs={'company_id': company.id})
    # print('******', url)
    # response = self.api_client.get(url)

    # assert response.status_code == status.HTTP_200_OK
    # assert response.json() == []
