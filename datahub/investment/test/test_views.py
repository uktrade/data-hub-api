from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.company.test.factories import CompanyFactory
from datahub.investment.test.factories import InvestmentProjectFactory


class InvestmentViewsTestCase(LeelooTestCase):
    """Company test case."""

    def test_list_projects(self):
        """Test successfully listing projects."""
        project = InvestmentProjectFactory()
        url = reverse('investment:v3:project')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(project.id)

    def test_create_project_success(self):
        """Test successfully creating a project."""
        url = reverse('investment:v3:project')
        request_data = {
            'name': 'project name',
            'description': 'project description',
            'nda_signed': False,
            'estimated_land_date': '2020-12-12',
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            },
            'phase': {
                'id': constants.InvestmentProjectPhase.assign_pm.value.id
            }
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['nda_signed'] == request_data['nda_signed']
        assert response_data['estimated_land_date'] == request_data['estimated_land_date']
        assert response_data['investment_type']['id'] == request_data['investment_type']['id']
        assert response_data['phase']['id'] == request_data['phase']['id']

    def test_patch_project_success(self):
        """Test successfully partially updating a project."""
        project = InvestmentProjectFactory()
        url = reverse('investment:v3:project-item', kwargs={'pk': project.pk})
        request_data = {
            'name': 'new name',
            'description': 'new description'
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
