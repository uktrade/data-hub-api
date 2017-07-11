"""Tests for investment views."""

import re
from datetime import datetime
from unittest.mock import patch

import pytest
import reversion
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (AdviserFactory, CompanyFactory,
                                            ContactFactory)
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.core.utils import executor
from datahub.documents.av_scan import virus_scan_document
from datahub.investment import views
from datahub.investment.models import InvestmentProjectTeamMember, IProjectDocument
from datahub.investment.test.factories import (
    InvestmentProjectFactory, InvestmentProjectTeamMemberFactory
)


class InvestmentViewsTestCase(LeelooTestCase):
    """Tests for the deprecated project, value, team and requirements views."""

    def test_list_projects_success(self):
        """Test successfully listing projects."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:project')
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
        url = reverse('api-v3:investment:project')
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
        intermediate_company = CompanyFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:project')
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
            'project_shareable': False,
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            },
            'stage': {
                'id': constants.InvestmentProjectStage.prospect.value.id
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
                'id': str(adviser.id)
            },
            'fdi_type': {
                'id': new_site_id
            },
            'investor_company': {
                'id': str(investor_company.id)
            },
            'intermediate_company': {
                'id': str(intermediate_company.id)
            },
            'referral_source_activity': {
                'id': constants.ReferralSourceActivity.cold_call.value.id
            },
            'referral_source_adviser': {
                'id': str(adviser.id)
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
        assert re.match('^DHP-\d+$', response_data['project_code'])

        assert (response_data['investment_type']['id'] == request_data[
            'investment_type']['id'])
        assert response_data['investor_company']['id'] == str(
            investor_company.id)
        assert response_data['intermediate_company']['id'] == str(
            intermediate_company.id)
        assert response_data['referral_source_adviser']['id'] == str(
            adviser.id)
        assert response_data['stage']['id'] == request_data['stage']['id']
        assert len(response_data['client_contacts']) == 2
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contact.id for contact in contacts)
        assert len(response_data['business_activities']) == 1
        assert (response_data['business_activities'][0]['id'] ==
                business_activity_id)

    def test_create_project_fail(self):
        """Test creating a project with missing required values."""
        url = reverse('api-v3:investment:project')
        request_data = {}
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'business_activities': ['This field is required.'],
            'client_contacts': ['This field is required.'],
            'client_relationship_manager': ['This field is required.'],
            'description': ['This field is required.'],
            'estimated_land_date': ['This field is required.'],
            'investor_company': ['This field is required.'],
            'investment_type': ['This field is required.'],
            'name': ['This field is required.'],
            'nda_signed': ['This field is required.'],
            'project_shareable': ['This field is required.'],
            'referral_source_activity': ['This field is required.'],
            'referral_source_adviser': ['This field is required.'],
            'sector': ['This field is required.']
        }

    def test_create_project_fail_none(self):
        """Test creating a project with None for required values."""
        url = reverse('api-v3:investment:project')
        request_data = {
            'business_activities': None,
            'client_contacts': None,
            'client_relationship_manager': None,
            'description': None,
            'estimated_land_date': None,
            'investor_company': None,
            'investment_type': None,
            'name': None,
            'nda_signed': None,
            'project_shareable': None,
            'referral_source_activity': None,
            'referral_source_adviser': None,
            'sector': None
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'business_activities': ['This field may not be null.'],
            'client_contacts': ['This field may not be null.'],
            'client_relationship_manager': ['This field may not be null.'],
            'description': ['This field may not be null.'],
            'estimated_land_date': ['This field may not be null.'],
            'investor_company': ['This field may not be null.'],
            'investment_type': ['This field may not be null.'],
            'name': ['This field may not be null.'],
            'nda_signed': ['This field may not be null.'],
            'project_shareable': ['This field may not be null.'],
            'referral_source_activity': ['This field may not be null.'],
            'referral_source_adviser': ['This field may not be null.'],
            'sector': ['This field may not be null.']
        }

    def test_create_project_fail_empty_to_many(self):
        """Test creating a project with empty to-many field values."""
        url = reverse('api-v3:investment:project')
        request_data = {
            'business_activities': [],
            'client_contacts': []
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data.keys() >= {
            'business_activities', 'client_contacts'
        }
        assert response_data['business_activities'] == [
            'This list may not be empty.']
        assert response_data['client_contacts'] == [
            'This list may not be empty.']

    def test_get_project_success(self):
        """Test successfully getting a project."""
        contacts = [ContactFactory().id, ContactFactory().id]
        project = InvestmentProjectFactory(client_contacts=contacts)
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
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
        assert (response_data['stage']['id'] == str(project.stage.id))
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contacts)

    def test_patch_project_conditional_failure(self):
        """Test updating a project w/ missing conditionally required value."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
        request_data = {
            'investment_type': {
                'id': str(constants.InvestmentType.fdi.value.id)
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'fdi_type': ['This field is required.']
        }

    def test_patch_project_success(self):
        """Test successfully partially updating a project."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
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

    def test_change_stage_assign_pm_failure(self):
        """Tests moving an incomplete project to the Assign PM stage."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'client_cannot_provide_total_investment': [
                'This field is required.'],
            'number_new_jobs': ['This field is required.'],
            'total_investment': ['This field is required.'],
            'client_considering_other_countries': ['This field is required.'],
            'client_requirements': ['This field is required.'],
            'site_decided': ['This field is required.'],
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
        }

    def test_change_stage_assign_pm_success(self):
        """Tests moving a complete project to the Assign PM stage."""
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            number_new_jobs=0,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id]
        )
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_stage_active_failure(self):
        """Tests moving an incomplete project to the Active stage."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.active.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'client_cannot_provide_total_investment': [
                'This field is required.'],
            'number_new_jobs': ['This field is required.'],
            'total_investment': ['This field is required.'],
            'client_considering_other_countries': ['This field is required.'],
            'client_requirements': ['This field is required.'],
            'site_decided': ['This field is required.'],
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
            'project_assurance_adviser': ['This field is required.'],
            'project_manager': ['This field is required.'],
        }

    def test_change_stage_active_success(self):
        """Tests moving a complete project to the Active stage."""
        adviser = AdviserFactory()
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            number_new_jobs=0,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id],
            project_assurance_adviser=adviser,
            project_manager=adviser
        )
        url = reverse('api-v3:investment:project-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.active.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

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
        url = reverse('api-v3:investment:value-item', kwargs={'pk': project.pk})
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
        url = reverse('api-v3:investment:value-item', kwargs={'pk': project.pk})
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
        url = reverse('api-v3:investment:requirements-item',
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
        url = reverse('api-v3:investment:requirements-item',
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
        pm_adviser = AdviserFactory(dit_team_id=crm_team.id)
        pa_adviser = AdviserFactory(dit_team_id=huk_team.id)
        project = InvestmentProjectFactory(
            project_manager_id=pm_adviser.id,
            project_assurance_adviser_id=pa_adviser.id
        )
        url = reverse('api-v3:investment:team-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'project_manager': {
                'id': str(pm_adviser.pk),
                'first_name': pm_adviser.first_name,
                'last_name': pm_adviser.last_name
            },
            'project_assurance_adviser': {
                'id': str(pa_adviser.pk),
                'first_name': pa_adviser.first_name,
                'last_name': pa_adviser.last_name
            },
            'project_manager_team': {
                'id': str(crm_team.id),
                'name': crm_team.name
            },
            'project_assurance_team': {
                'id': str(huk_team.id),
                'name': huk_team.name
            },
            'team_members': [],
            'team_complete': True
        }

    def test_get_team_empty(self):
        """Test successfully getting an empty project requirements object."""
        project = InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.assign_pm.value.id
        )
        url = reverse('api-v3:investment:team-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'project_manager': None,
            'project_assurance_adviser': None,
            'project_manager_team': None,
            'project_assurance_team': None,
            'team_complete': False,
            'team_members': []
        }

    def test_patch_team_success(self):
        """Test successfully partially updating a requirements object."""
        crm_team = constants.Team.crm.value
        huk_team = constants.Team.healthcare_uk.value
        adviser_1 = AdviserFactory(dit_team_id=crm_team.id)
        adviser_2 = AdviserFactory(dit_team_id=huk_team.id)
        project = InvestmentProjectFactory(
            project_manager_id=adviser_1.id,
            project_assurance_adviser_id=adviser_2.id
        )
        url = reverse('api-v3:investment:team-item',
                      kwargs={'pk': project.pk})
        request_data = {
            'project_manager': {
                'id': str(adviser_2.id)
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'project_manager': {
                'id': str(adviser_2.pk),
                'first_name': adviser_2.first_name,
                'last_name': adviser_2.last_name
            },
            'project_assurance_adviser': {
                'id': str(adviser_2.pk),
                'first_name': adviser_2.first_name,
                'last_name': adviser_2.last_name
            },
            'project_manager_team': {
                'id': str(huk_team.id),
                'name': huk_team.name
            },
            'project_assurance_team': {
                'id': str(huk_team.id),
                'name': huk_team.name
            },
            'team_members': [],
            'team_complete': True
        }


class UnifiedViewsTestCase(LeelooTestCase):
    """Tests for the unified investment views."""

    def test_list_projects_success(self):
        """Test successfully listing projects."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-collection')
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
        url = reverse('api-v3:investment:investment-collection')
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
        intermediate_company = CompanyFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:investment-collection')
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
            'project_shareable': False,
            'likelihood_of_landing': 60,
            'priority': '1_low',
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            },
            'stage': {
                'id': constants.InvestmentProjectStage.prospect.value.id
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
                'id': str(adviser.id)
            },
            'fdi_type': {
                'id': new_site_id
            },
            'investor_company': {
                'id': str(investor_company.id)
            },
            'intermediate_company': {
                'id': str(intermediate_company.id)
            },
            'referral_source_activity': {
                'id': constants.ReferralSourceActivity.cold_call.value.id
            },
            'referral_source_adviser': {
                'id': str(adviser.id)
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
        assert (response_data['likelihood_of_landing'] == request_data['likelihood_of_landing'])
        assert response_data['priority'] == request_data['priority']
        assert re.match('^DHP-\d+$', response_data['project_code'])

        assert (response_data['investment_type']['id'] == request_data[
            'investment_type']['id'])
        assert response_data['investor_company']['id'] == str(
            investor_company.id)
        assert response_data['intermediate_company']['id'] == str(
            intermediate_company.id)
        assert response_data['referral_source_adviser']['id'] == str(
            adviser.id)
        assert response_data['stage']['id'] == request_data['stage']['id']
        assert len(response_data['client_contacts']) == 2
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contact.id for contact in contacts)
        assert len(response_data['business_activities']) == 1
        assert (response_data['business_activities'][0]['id'] ==
                business_activity_id)

    def test_create_project_fail(self):
        """Test creating a project with missing required values."""
        url = reverse('api-v3:investment:investment-collection')
        request_data = {}
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'business_activities': ['This field is required.'],
            'client_contacts': ['This field is required.'],
            'client_relationship_manager': ['This field is required.'],
            'description': ['This field is required.'],
            'estimated_land_date': ['This field is required.'],
            'investor_company': ['This field is required.'],
            'investment_type': ['This field is required.'],
            'name': ['This field is required.'],
            'nda_signed': ['This field is required.'],
            'project_shareable': ['This field is required.'],
            'referral_source_activity': ['This field is required.'],
            'referral_source_adviser': ['This field is required.'],
            'sector': ['This field is required.']
        }

    def test_create_project_fail_none(self):
        """Test creating a project with None for required values."""
        url = reverse('api-v3:investment:investment-collection')
        request_data = {
            'business_activities': None,
            'client_contacts': None,
            'client_relationship_manager': None,
            'description': None,
            'estimated_land_date': None,
            'investor_company': None,
            'investment_type': None,
            'name': None,
            'nda_signed': None,
            'project_shareable': None,
            'referral_source_activity': None,
            'referral_source_adviser': None,
            'sector': None
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'business_activities': ['This field may not be null.'],
            'client_contacts': ['This field may not be null.'],
            'client_relationship_manager': ['This field may not be null.'],
            'description': ['This field may not be null.'],
            'estimated_land_date': ['This field may not be null.'],
            'investor_company': ['This field may not be null.'],
            'investment_type': ['This field may not be null.'],
            'name': ['This field may not be null.'],
            'nda_signed': ['This field may not be null.'],
            'project_shareable': ['This field may not be null.'],
            'referral_source_activity': ['This field may not be null.'],
            'referral_source_adviser': ['This field may not be null.'],
            'sector': ['This field may not be null.']
        }

    def test_create_project_fail_empty_to_many(self):
        """Test creating a project with empty to-many field values."""
        url = reverse('api-v3:investment:investment-collection')
        request_data = {
            'business_activities': [],
            'client_contacts': []
        }
        response = self.api_client.post(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data.keys() >= {
            'business_activities', 'client_contacts'
        }
        assert response_data['business_activities'] == ['This list may not be empty.']
        assert response_data['client_contacts'] == ['This list may not be empty.']

    def test_get_project_success(self):
        """Test successfully getting a project."""
        contacts = [ContactFactory().id, ContactFactory().id]
        project = InvestmentProjectFactory(client_contacts=contacts)
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['id'] == str(project.id)
        assert response_data['name'] == project.name
        assert response_data['description'] == project.description
        assert response_data['likelihood_of_landing'] == project.likelihood_of_landing
        assert response_data['nda_signed'] == project.nda_signed
        assert response_data['project_code'] == project.project_code
        assert (response_data['estimated_land_date'] ==
                str(project.estimated_land_date))
        assert (response_data['investment_type']['id'] ==
                str(project.investment_type.id))
        assert (response_data['stage']['id'] == str(project.stage.id))
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == sorted(contacts)

    def test_patch_project_conditional_failure(self):
        """Test updating a project w/ missing conditionally required value."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'investment_type': {
                'id': str(constants.InvestmentType.fdi.value.id)
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'fdi_type': ['This field is required.']
        }

    def test_patch_likelihood_of_landing_too_low(self):
        """Test updating a project with a likelihood_of_landing below 0."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'likelihood_of_landing': -10
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'likelihood_of_landing': ['Ensure this value is greater than or equal to 0.']
        }

    def test_patch_likelihood_of_landing_too_high(self):
        """Test updating a project with a likelihood_of_landing above 100."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'likelihood_of_landing': 110
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'likelihood_of_landing': ['Ensure this value is less than or equal to 100.']
        }

    def test_patch_priority_invalid_value(self):
        """Test updating a project with an invalid priority."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'priority': '6_extremely_urgent'
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'priority': ['"6_extremely_urgent" is not a valid choice.']
        }

    def test_patch_project_success(self):
        """Test successfully partially updating a project."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
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

    def test_change_stage_assign_pm_failure(self):
        """Tests moving an incomplete project to the Assign PM stage."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'client_cannot_provide_total_investment': [
                'This field is required.'],
            'number_new_jobs': ['This field is required.'],
            'total_investment': ['This field is required.'],
            'client_considering_other_countries': ['This field is required.'],
            'client_requirements': ['This field is required.'],
            'site_decided': ['This field is required.'],
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
        }

    def test_change_stage_assign_pm_success(self):
        """Tests moving a complete project to the Assign PM stage."""
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            number_new_jobs=0,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id]
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_stage_active_failure(self):
        """Tests moving an incomplete project to the Active stage."""
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id]
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.active.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'client_cannot_provide_total_investment': [
                'This field is required.'],
            'number_new_jobs': ['This field is required.'],
            'total_investment': ['This field is required.'],
            'client_considering_other_countries': ['This field is required.'],
            'client_requirements': ['This field is required.'],
            'site_decided': ['This field is required.'],
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
            'project_assurance_adviser': ['This field is required.'],
            'project_manager': ['This field is required.'],
        }

    def test_change_stage_active_success(self):
        """Tests moving a complete project to the Active stage."""
        adviser = AdviserFactory()
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            number_new_jobs=0,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id],
            project_assurance_adviser=adviser,
            project_manager=adviser
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.active.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_change_stage_verify_win_failure(self):
        """Tests moving a partially complete project to the 'Verify win' stage."""
        adviser = AdviserFactory()
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            number_new_jobs=10,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id],
            project_assurance_adviser=adviser,
            project_manager=adviser
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.verify_win.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'government_assistance': ['This field is required.'],
            'number_safeguarded_jobs': ['This field is required.'],
            'r_and_d_budget': ['This field is required.'],
            'non_fdi_r_and_d_budget': ['This field is required.'],
            'new_tech_to_uk': ['This field is required.'],
            'export_revenue': ['This field is required.'],
            'address_line_1': ['This field is required.'],
            'address_line_2': ['This field is required.'],
            'address_line_postcode': ['This field is required.'],
            'average_salary': ['This field is required.'],
            'client_cannot_provide_foreign_investment': ['This field is required.'],
            'foreign_equity_investment': ['This field is required.'],
        }

    def test_change_stage_verify_win_success(self):
        """Tests moving a complete project to the 'Verify win' stage."""
        adviser = AdviserFactory()
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            client_cannot_provide_foreign_investment=False,
            foreign_equity_investment=200,
            number_new_jobs=10,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id],
            project_assurance_adviser=adviser,
            project_manager=adviser,
            government_assistance=False,
            number_safeguarded_jobs=0,
            r_and_d_budget=True,
            non_fdi_r_and_d_budget=True,
            new_tech_to_uk=True,
            export_revenue=True,
            address_line_1='12 London Road',
            address_line_2='London',
            address_line_postcode='SW1A 2AA',
            average_salary_id=constants.SalaryRange.below_25000.value.id
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.verify_win.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK

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
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['client_cannot_provide_foreign_investment'] is False
        assert response_data['client_cannot_provide_total_investment'] is False
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
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
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
        url = reverse('api-v3:investment:investment-item',
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
        url = reverse('api-v3:investment:investment-item',
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
        pm_adviser = AdviserFactory(dit_team_id=crm_team.id)
        pa_adviser = AdviserFactory(dit_team_id=huk_team.id)
        project = InvestmentProjectFactory(
            project_manager_id=pm_adviser.id,
            project_assurance_adviser_id=pa_adviser.id
        )
        url = reverse('api-v3:investment:investment-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['project_manager'] == {
            'id': str(pm_adviser.pk),
            'first_name': pm_adviser.first_name,
            'last_name': pm_adviser.last_name
        }
        assert response_data['project_assurance_adviser'] == {
            'id': str(pa_adviser.pk),
            'first_name': pa_adviser.first_name,
            'last_name': pa_adviser.last_name
        }
        assert response_data['project_manager_team'] == {
            'id': str(crm_team.id),
            'name': crm_team.name
        }
        assert response_data['project_assurance_team'] == {
            'id': str(huk_team.id),
            'name': huk_team.name
        }
        assert response_data['team_members'] == []
        assert response_data['team_complete'] is True

    def test_get_team_empty(self):
        """Test successfully getting an empty project requirements object."""
        project = InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.assign_pm.value.id
        )
        url = reverse('api-v3:investment:investment-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['project_manager'] is None
        assert response_data['project_assurance_adviser'] is None
        assert response_data['project_manager_team'] is None
        assert response_data['project_assurance_team'] is None
        assert response_data['team_members'] == []
        assert response_data['team_complete'] is False

    def test_patch_team_success(self):
        """Test successfully partially updating a requirements object."""
        crm_team = constants.Team.crm.value
        huk_team = constants.Team.healthcare_uk.value
        adviser_1 = AdviserFactory(dit_team_id=crm_team.id)
        adviser_2 = AdviserFactory(dit_team_id=huk_team.id)
        project = InvestmentProjectFactory(
            project_manager_id=adviser_1.id,
            project_assurance_adviser_id=adviser_2.id
        )
        url = reverse('api-v3:investment:investment-item',
                      kwargs={'pk': project.pk})
        request_data = {
            'project_manager': {
                'id': str(adviser_2.id)
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['project_manager'] == {
            'id': str(adviser_2.pk),
            'first_name': adviser_2.first_name,
            'last_name': adviser_2.last_name
        }
        assert response_data['project_assurance_adviser'] == {
            'id': str(adviser_2.pk),
            'first_name': adviser_2.first_name,
            'last_name': adviser_2.last_name
        }
        assert response_data['project_manager_team'] == {
            'id': str(huk_team.id),
            'name': huk_team.name
        }
        assert response_data['project_assurance_team'] == {
            'id': str(huk_team.id),
            'name': huk_team.name
        }
        assert response_data['team_members'] == []
        assert response_data['team_complete'] is True

    def test_get_phase_backwards_compatibility(self):
        """Tests that phase works as an alias for stage with GET."""
        project = InvestmentProjectFactory(
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['phase'] == {
            'id': constants.InvestmentProjectStage.prospect.value.id,
            'name': constants.InvestmentProjectStage.prospect.value.name
        }
        assert response_data['phase'] == response_data['stage']

    def test_patch_phase_backwards_compatibility(self):
        """Tests that phase works as an alias for stage with PATCH."""
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
            client_contacts=[ContactFactory().id, ContactFactory().id],
            client_cannot_provide_total_investment=False,
            total_investment=100,
            number_new_jobs=0,
            client_considering_other_countries=False,
            client_requirements='client reqs',
            site_decided=False,
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id]
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'phase': {
                'id': constants.InvestmentProjectStage.assign_pm.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['phase'] == {
            'id': constants.InvestmentProjectStage.assign_pm.value.id,
            'name': constants.InvestmentProjectStage.assign_pm.value.name
        }
        assert response_data['phase'] == response_data['stage']


class TeamMemberViewsTestCase(LeelooTestCase):
    """Tests for the team member views."""

    def test_add_team_member_success(self):
        """Tests adding a team member to a project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        request_data = {
            'adviser': {
                'id': str(adviser.pk)
            },
            'role': 'Sector adviser'
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['adviser']['id'] == str(adviser.pk)
        assert response_data['role'] == 'Sector adviser'

    def test_add_duplicate_team_member(self):
        """Tests adding a duplicate team member to a project."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-collection', kwargs={
            'project_pk': team_member.investment_project.pk,
        })
        request_data = {
            'adviser': {
                'id': str(team_member.adviser.pk)
            },
            'role': 'Sector adviser'
        }
        response = self.api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'non_field_errors': ['The fields investment_project, adviser must make a unique set.']
        }

    def test_get_team_member_success(self):
        """Tests getting a project team member."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['role'] == team_member.role

    def test_patch_team_member_success(self):
        """Tests updating a project team member's role."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        request_data = {
            'role': 'updated role'
        }
        response = self.api_client.patch(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['role'] == request_data['role']

    def test_delete_team_member_success(self):
        """Tests deleting a project team member."""
        project = InvestmentProjectFactory()
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_members[0].investment_project.pk,
            'adviser_pk': team_members[0].adviser.pk
        })
        response = self.api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        new_team_members = InvestmentProjectTeamMember.objects.filter(investment_project=project)
        assert new_team_members.count() == 1
        assert str(new_team_members[0].adviser.pk) == team_members[1].adviser.pk


class AuditLogViewTestCase(LeelooTestCase):
    """Tests for the audit log view."""

    def test_audit_log_view(self):
        """Test retrieval of audit log."""
        user = self.get_user()

        initial_datetime = datetime.utcnow()
        with reversion.create_revision():
            iproject = InvestmentProjectFactory(
                description='Initial desc',
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(user)

        changed_datetime = datetime.utcnow()
        with reversion.create_revision():
            iproject.description = 'New desc'
            iproject.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(user)

        url = reverse('api-v3:investment:audit-item',
                      kwargs={'pk': iproject.pk})

        response = self.api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1, 'Only one entry in audit log'
        entry = response_data[0]

        assert entry['user']['name'] == user.name, 'Valid user captured'
        assert entry['comment'] == 'Changed', 'Comments can be set manually'
        assert entry['timestamp'] == changed_datetime.isoformat(), 'TS can be set manually'
        assert entry['changes']['description'] == ['Initial desc', 'New desc'], 'Changes are reflected'


class ArchiveViewsTestCase(LeelooTestCase):
    """Tests for the archive and unarchive views."""

    def test_archive_project_success(self):
        """Tests archiving a project."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.post(url, format='json', data={
            'reason': 'archive reason'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is True
        assert response_data['archived_by']['id'] == str(self.user.pk)
        assert response_data['archived_reason'] == 'archive reason'

    def test_archive_fail_no_reason(self):
        """Test archive a project without providing a reason."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.post(url, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.']
        }

    def test_archive_fail_blank_reason(self):
        """Test archive a project without providing a reason."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.post(url, format='json', data={
            'reason': ''
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field may not be blank.']
        }

    def test_archive_fail_null_reason(self):
        """Test archive a project with a null reason."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.post(url, format='json', data={
            'reason': None
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field may not be null.']
        }

    def test_unarchive_project_success(self):
        """Tests unarchiving a project."""
        project = InvestmentProjectFactory(
            archived=True, archived_reason='reason'
        )
        url = reverse('api-v3:investment:unarchive-item',
                      kwargs={'pk': project.pk})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is False
        assert response_data['archived_by'] is None
        assert response_data['archived_reason'] == ''


class DocumentViewsTestCase(LeelooTestCase):
    """Tests for the document views."""

    def test_documents_list_is_filtered_by_project(self):
        """Tests viewset filtering."""
        project1 = InvestmentProjectFactory()
        project2 = InvestmentProjectFactory()

        IProjectDocument.create_from_declaration_request(project1, 'fdi_type', 'test.txt')
        doc2 = IProjectDocument.create_from_declaration_request(project2, 'fdi_type', 'test.txt')

        url = reverse('api-v3:investment:document-collection',
                      kwargs={'project_pk': project2.pk})

        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.data
        assert response_data['count'] == 1
        assert len(response_data['results']) == 1
        assert response_data['results'][0]['id'] == str(doc2.pk)

    def test_document_creation(self):
        """Test document creation can omit project PK (Will be inferred from URL)."""
        project = InvestmentProjectFactory()

        url = reverse('api-v3:investment:document-collection',
                      kwargs={'project_pk': project.pk})

        response = self.api_client.post(url, format='json', data={
            'filename': 'test.txt',
            'doc_type': 'fdi_type',
            'project': str(project.pk),
        })

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data
        assert response_data['doc_type'] == 'fdi_type'
        assert response_data['filename'] == 'test.txt'
        assert response_data['project']['id'] == str(project.pk)

        doc = IProjectDocument.objects.get(pk=response_data['id'])
        assert doc.filename == 'test.txt'
        assert doc.doc_type == 'fdi_type'
        assert str(doc.project.pk) == str(project.pk)
        assert 'signed_upload_url' in response.data

    def test_document_retrieval(self):
        """Tests retrieval of individual document."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(project, 'fdi_type', 'test.txt')

        url = reverse('api-v3:investment:document-item',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(doc.pk)
        assert response.data['project'] == {
            'id': str(project.pk),
            'name': project.name,
        }
        assert response.data['doc_type'] == 'fdi_type'
        assert response.data['filename'] == 'test.txt'
        assert 'signed_url' in response.data

    @patch.object(executor, 'submit')
    def test_document_upload_status(self, mock_submit):
        """Tests setting of document upload status to complete.

        Checks that a virus scan of the document was scheduled. Virus scanning is
        tested separately in the documents app.
        """
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(project, 'fdi_type', 'test.txt')

        url = reverse('api-v3:investment:document-item-callback',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.post(url, format='json', data={
            'status': 'success'
        })
        assert response.status_code == status.HTTP_200_OK
        mock_submit.assert_called_once_with(virus_scan_document, str(doc.pk))

    def test_document_upload_status_wrong_status(self):
        """Tests request validation in the document status endpoint."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(project, 'fdi_type', 'test.txt')

        url = reverse('api-v3:investment:document-item-callback',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.post(url, format='json', data={
            'status': '123456'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.json()

    def test_document_upload_status_no_status(self):
        """Tests request validation in the document status endpoint."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(project, 'fdi_type', 'test.txt')

        url = reverse('api-v3:investment:document-item-callback',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.post(url, format='json', data={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.json()


@pytest.mark.parametrize('view_set', (views.IProjectTeamViewSet,
                                      views.IProjectRequirementsViewSet,
                                      views.IProjectViewSet,
                                      views.IProjectValueViewSet,
                                      views.IProjectAuditViewSet))
def test_view_set_name(view_set):
    """Test that the view name is a string."""
    assert isinstance(view_set().get_view_name(), str)
