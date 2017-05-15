"""Tests for investment views."""

import re

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (AdvisorFactory, CompanyFactory,
                                            ContactFactory)
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.investment import views
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

    def test_list_projects_investor_company_success(self):
        """Test successfully listing projects for an investor company."""
        company = CompanyFactory()
        project = InvestmentProjectFactory(investor_company_id=company.id)
        InvestmentProjectFactory()
        url = reverse('investment:v3:project')
        response = self.api_client.get(url, {
            'investor_company_id': str(company.id)
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(project.id)

    def test_create_project_complete_success(self):
        """Test successfully creating a project."""
        contacts = [ContactFactory(), ContactFactory()]
        investor_company = CompanyFactory()
        recipient_company = CompanyFactory()
        intermediate_company = CompanyFactory()
        advisor = AdvisorFactory()
        url = reverse('investment:v3:project')
        aerospace_id = constants.Sector.aerospace_assembly_aircraft.value.id
        new_site_id = (constants.FDIType.creation_of_new_site_or_activity
                       .value.id)
        retail_business_activity = constants.InvestmentBusinessActivity.retail
        business_activity_id = retail_business_activity.value.id
        request_data = {
            'name': 'project name',
            'description': 'project description',
            'nda_signed': False,
            'estimated_land_date': '2020-12-12',
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            },
            'phase': {
                'id': constants.InvestmentProjectPhase.prospect.value.id
            },
            'business_activities': [{
                'id': business_activity_id
            }],
            'client_contacts': [{
                'id': str(contacts[0].id)
            }, {
                'id': str(contacts[1].id)
            }],
            'client_relationship_manager': {
                'id': str(advisor.id)
            },
            'fdi_type': {
                'id': new_site_id
            },
            'investor_company': {
                'id': str(investor_company.id)
            },
            'investment_recipient_company': {
                'id': str(recipient_company.id)
            },
            'intermediate_company': {
                'id': str(intermediate_company.id)
            },
            'referral_source_activity': {
                'id': constants.ReferralSourceActivity.cold_call.value.id
            },
            'referral_source_advisor': {
                'id': str(advisor.id)
            },
            'sector': {
                'id': str(aerospace_id)
            }
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['nda_signed'] == request_data['nda_signed']
        assert (response_data['estimated_land_date'] == request_data[
            'estimated_land_date'])
        assert response_data['project_section_complete'] is True
        assert re.match('^DHP-\d+$', response_data['project_code'])

        assert (response_data['investment_type']['id'] == request_data[
            'investment_type']['id'])
        assert response_data['investor_company']['id'] == str(
            investor_company.id)
        assert response_data['investment_recipient_company']['id'] == str(
            recipient_company.id)
        assert response_data['intermediate_company']['id'] == str(
            intermediate_company.id)
        assert response_data['referral_source_advisor']['id'] == str(
            advisor.id)
        assert response_data['phase']['id'] == request_data['phase']['id']
        assert len(response_data['client_contacts']) == 2
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contact.id for contact in contacts)
        assert len(response_data['business_activities']) == 1
        assert (response_data['business_activities'][0]['id'] ==
                business_activity_id)

    def test_create_project_minimal_success(self):
        """Test successfully creating a project with minimal data."""
        url = reverse('investment:v3:project')
        request_data = {
            'name': 'project name',
            'description': 'project description',
            'nda_signed': False,
            'estimated_land_date': '2020-12-12',
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            }
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['name'] == request_data['name']
        assert response_data['description'] == request_data['description']
        assert response_data['nda_signed'] == request_data['nda_signed']
        assert (response_data['estimated_land_date'] == request_data[
            'estimated_land_date'])
        assert response_data['project_section_complete'] is False
        assert re.match('^DHP-\d+$', response_data['project_code'])

        assert (response_data['phase']['id'] ==
                constants.InvestmentProjectPhase.prospect.value.id)
        assert (response_data['investment_type']['id'] == request_data[
            'investment_type']['id'])

    def test_create_project_fail(self):
        """Test creating a project with missing required values."""
        url = reverse('investment:v3:project')
        request_data = {
            'name': 'project name'
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'description': ['This field is required.'],
            'investment_type': ['This field is required.'],
            'estimated_land_date': ['This field is required.']
        }

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
        assert response_data['project_code'] == project.project_code
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

    def test_change_phase_failure(self):
        """Tests moving an incomplete project to the Assign PM phase."""
        project = InvestmentProjectFactory(
            sector_id=None
        )
        url = reverse('investment:v3:project-item', kwargs={'pk': project.pk})
        request_data = {
            'phase': {
                'id': constants.InvestmentProjectPhase.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'business_activities': ['This field is required.'],
            'client_contacts': ['This field is required.'],
            'client_relationship_manager': ['This field is required.'],
            'fdi_type': ['This field is required.'],
            'investor_company': ['This field is required.'],
            'referral_source_activity': ['This field is required.'],
            'referral_source_advisor': ['This field is required.'],
            'sector': ['This field is required.'],
            'client_cannot_provide_foreign_investment': [
                'This field is required.'],
            'client_cannot_provide_total_investment': [
                'This field is required.'],
            'export_revenue': ['This field is required.'],
            'foreign_equity_investment': ['This field is required.'],
            'government_assistance': ['This field is required.'],
            'new_tech_to_uk': ['This field is required.'],
            'non_fdi_r_and_d_budget': ['This field is required.'],
            'number_new_jobs': ['This field is required.'],
            'number_safeguarded_jobs': ['This field is required.'],
            'r_and_d_budget': ['This field is required.'],
            'total_investment': ['This field is required.'],
            'client_considering_other_countries': ['This field is required.'],
            'client_requirements': ['This field is required.'],
            'site_decided': ['This field is required.'],
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
        }

    def test_change_phase_success(self):
        """Tests moving a complete project to the Assign PM phase."""
        advisor = AdvisorFactory()
        company = CompanyFactory()
        new_site_id = (constants.FDIType.creation_of_new_site_or_activity
                       .value.id)
        cold_call_id = constants.ReferralSourceActivity.cold_call.value.id
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            business_activities=[
                constants.InvestmentBusinessActivity.retail.value.id
            ],
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_relationship_manager_id=advisor.id,
            fdi_type_id=new_site_id,
            investor_company_id=company.id,
            referral_source_activity_id=cold_call_id,
            referral_source_advisor_id=advisor.id,
            client_cannot_provide_foreign_investment=False,
            client_cannot_provide_total_investment=False,
            total_investment=100,
            foreign_equity_investment=100,
            government_assistance=True,
            number_new_jobs=0,
            number_safeguarded_jobs=0,
            r_and_d_budget=False,
            non_fdi_r_and_d_budget=False,
            new_tech_to_uk=False,
            export_revenue=True,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id]
        )
        url = reverse('investment:v3:project-item', kwargs={'pk': project.pk})
        request_data = {
            'phase': {
                'id': constants.InvestmentProjectPhase.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['project_section_complete'] is True

    def test_get_value_success(self):
        """Test successfully getting a project value object."""
        project = InvestmentProjectFactory(
            client_cannot_provide_foreign_investment=False,
            client_cannot_provide_total_investment=False,
            total_investment=100,
            foreign_equity_investment=100,
            government_assistance=True,
            number_new_jobs=0,
            number_safeguarded_jobs=10,
            r_and_d_budget=False,
            non_fdi_r_and_d_budget=False,
            new_tech_to_uk=False,
            export_revenue=True
        )
        url = reverse('investment:v3:value-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert (response_data['client_cannot_provide_foreign_investment'] is
                False)
        assert (response_data['client_cannot_provide_total_investment'] is
                False)
        assert response_data['total_investment'] == '100'
        assert response_data['foreign_equity_investment'] == '100'
        assert response_data['government_assistance'] is True
        assert response_data['total_investment'] == '100'
        assert response_data['number_new_jobs'] == 0
        assert response_data['number_safeguarded_jobs'] == 10
        assert response_data['r_and_d_budget'] is False
        assert response_data['non_fdi_r_and_d_budget'] is False
        assert response_data['new_tech_to_uk'] is False
        assert response_data['export_revenue'] is True
        assert response_data['value_complete'] is True

    def test_patch_value_success(self):
        """Test successfully partially updating a project value object."""
        salary_id = constants.SalaryRange.below_25000.value.id
        project = InvestmentProjectFactory(total_investment=999,
                                           number_new_jobs=100)
        url = reverse('investment:v3:value-item', kwargs={'pk': project.pk})
        request_data = {
            'number_new_jobs': 555,
            'average_salary': {'id': salary_id},
            'government_assistance': True
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['number_new_jobs'] == 555
        assert response_data['government_assistance'] is True
        assert response_data['total_investment'] == '999'
        assert response_data['value_complete'] is False
        assert response_data['average_salary']['id'] == salary_id

    def test_get_requirements_success(self):
        """Test successfully getting a project requirements object."""
        countries = [
            constants.Country.united_kingdom.value.id,
            constants.Country.united_states.value.id
        ]
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        uk_region_locations = [constants.UKRegion.england.value.id]
        project = InvestmentProjectFactory(
            client_requirements='client reqs',
            site_decided=True,
            address_line_1='address 1',
            client_considering_other_countries=True,
            competitor_countries=countries,
            strategic_drivers=strategic_drivers,
            uk_region_locations=uk_region_locations
        )
        url = reverse('investment:v3:requirements-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['client_requirements'] == 'client reqs'
        assert response_data['site_decided'] is True
        assert response_data['client_considering_other_countries'] is True
        assert response_data['requirements_complete'] is True
        assert response_data['address_line_1'] == 'address 1'
        assert sorted(country['id'] for country in response_data[
            'competitor_countries']) == sorted(countries)
        assert sorted(driver['id'] for driver in response_data[
            'strategic_drivers']) == sorted(strategic_drivers)

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
        assert response_data['requirements_complete'] is False
        assert response_data['client_requirements'] == 'client reqs'
        assert response_data['site_decided'] is True
        assert response_data['address_line_1'] == 'address 1 new'
        assert response_data['address_line_2'] == 'address 2 new'

    def test_get_team_success(self):
        """Test successfully getting a project requirements object."""
        crm_team = constants.Team.crm.value
        huk_team = constants.Team.healthcare_uk.value
        pm_advisor = AdvisorFactory(dit_team_id=crm_team.id)
        pa_advisor = AdvisorFactory(dit_team_id=huk_team.id)
        project = InvestmentProjectFactory(
            project_manager_id=pm_advisor.id,
            project_assurance_advisor_id=pa_advisor.id
        )
        url = reverse('investment:v3:team-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'project_manager': {
                'id': str(pm_advisor.pk),
                'first_name': pm_advisor.first_name,
                'last_name': pm_advisor.last_name
            },
            'project_assurance_advisor': {
                'id': str(pa_advisor.pk),
                'first_name': pa_advisor.first_name,
                'last_name': pa_advisor.last_name
            },
            'project_manager_team': {
                'id': str(crm_team.id),
                'name': crm_team.name
            },
            'project_assurance_team': {
                'id': str(huk_team.id),
                'name': huk_team.name
            }
        }

    def test_patch_team_success(self):
        """Test successfully partially updating a requirements object."""
        crm_team = constants.Team.crm.value
        huk_team = constants.Team.healthcare_uk.value
        advisor_1 = AdvisorFactory(dit_team_id=crm_team.id)
        advisor_2 = AdvisorFactory(dit_team_id=huk_team.id)
        project = InvestmentProjectFactory(
            project_manager_id=advisor_1.id,
            project_assurance_advisor_id=advisor_2.id
        )
        url = reverse('investment:v3:team-item',
                      kwargs={'pk': project.pk})
        request_data = {
            'project_manager': {
                'id': str(advisor_2.id)
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'project_manager': {
                'id': str(advisor_2.pk),
                'first_name': advisor_2.first_name,
                'last_name': advisor_2.last_name
            },
            'project_assurance_advisor': {
                'id': str(advisor_2.pk),
                'first_name': advisor_2.first_name,
                'last_name': advisor_2.last_name
            },
            'project_manager_team': {
                'id': str(huk_team.id),
                'name': huk_team.name
            },
            'project_assurance_team': {
                'id': str(huk_team.id),
                'name': huk_team.name
            }
        }


@pytest.mark.parametrize('view_set', (views.IProjectTeamViewSet,
                                      views.IProjectRequirementsViewSet,
                                      views.IProjectViewSet,
                                      views.IProjectValueViewSet))
def test_view_set_name(view_set):
    """Test that the view name is a string."""
    assert isinstance(view_set().get_view_name(), str)
