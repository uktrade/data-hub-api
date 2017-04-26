from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.investment.test.factories import InvestmentProjectFactory


class InvestmentViewsTestCase(LeelooTestCase):
    """Company test case."""

    def test_list_projects_success(self):
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
        for key in ('name', 'description', 'nda_signed',
                    'estimated_land_date'):
            assert response_data[key] == request_data[key]
        for key in ('investment_type', 'phase'):
            assert response_data[key]['id'] == request_data[key]['id']

    def test_get_project_success(self):
        """Test successfully getting a project."""
        project = InvestmentProjectFactory()
        url = reverse('investment:v3:project-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['id'] == str(project.id)
        assert response_data['name'] == project.name
        assert response_data['description'] == project.description
        assert response_data['nda_signed'] == project.nda_signed
        assert (response_data['estimated_land_date'] ==
                str(project.estimated_land_date))
        assert (response_data['investment_type']['id'] ==
                str(project.investment_type.id))
        assert (response_data['phase']['id'] == str(project.phase.id))

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

    def test_get_value_success(self):
        """Test successfully getting a project value object."""
        project = InvestmentProjectFactory(total_investment=999,
                                           number_new_jobs=100)
        url = reverse('investment:v3:value-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['total_investment'] == '999'
        assert response_data['number_new_jobs'] == 100

    def test_patch_value_success(self):
        """Test successfully partially updating a project value object."""
        project = InvestmentProjectFactory(total_investment=999,
                                           number_new_jobs=100)
        url = reverse('investment:v3:value-item', kwargs={'pk': project.pk})
        request_data = {
            'number_new_jobs': 555,
            'government_assistance': True
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['number_new_jobs'] == 555
        assert response_data['government_assistance'] is True
        assert response_data['total_investment'] == '999'
