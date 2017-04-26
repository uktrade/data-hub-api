from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import ContactFactory
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
        contacts = [ContactFactory(), ContactFactory()]
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
            },
            'client_contacts': [{
                'id': str(contacts[0].id)
            }, {
                'id': str(contacts[1].id)
            }]
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['nda_signed'] == request_data['nda_signed']
        assert (response_data['estimated_land_date'] == request_data[
            'estimated_land_date'])
        assert (response_data['investment_type']['id'] == request_data[
            'investment_type']['id'])
        assert response_data['phase']['id'] == request_data['phase']['id']
        assert len(response_data['client_contacts']) == 2
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contact.id for contact in contacts)

    def test_get_project_success(self):
        """Test successfully getting a project."""
        contacts = [ContactFactory().id, ContactFactory().id]
        project = InvestmentProjectFactory(client_contacts=contacts)
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
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contacts)

    def test_patch_project_success(self):
        """Test successfully partially updating a project."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('investment:v3:project-item', kwargs={'pk': project.pk})
        new_contact = ContactFactory()
        request_data = {
            'name': 'new name',
            'description': 'new description',
            'client_contacts': [{
                'id': str(new_contact.id)
            }]
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert len(response_data['client_contacts']) == 1
        assert response_data['client_contacts'][0]['id'] == str(new_contact.id)

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

    def test_get_requirements_success(self):
        """Test successfully getting a project requirements object."""
        countries = [
            constants.Country.united_kingdom.value.id,
            constants.Country.united_states.value.id
        ]
        project = InvestmentProjectFactory(client_requirements='client reqs',
                                           site_decided=True,
                                           address_line_1='address 1',
                                           competitor_countries=countries)
        url = reverse('investment:v3:requirements-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['client_requirements'] == 'client reqs'
        assert response_data['site_decided'] is True
        assert response_data['address_line_1'] == 'address 1'
        assert sorted(country['id'] for country in response_data[
            'competitor_countries']) == sorted(countries)

    def test_patch_requirements_success(self):
        """Test successfully partially updating a requirements object."""
        project = InvestmentProjectFactory(client_requirements='client reqs',
                                           site_decided=True,
                                           address_line_1='address 1')
        url = reverse('investment:v3:requirements-item',
                      kwargs={'pk': project.pk})
        request_data = {
            'address_line_1': 'address 1 new',
            'address_line_2': 'address 2 new'
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['client_requirements'] == 'client reqs'
        assert response_data['site_decided'] is True
        assert response_data['address_line_1'] == 'address 1 new'
        assert response_data['address_line_2'] == 'address 2 new'
