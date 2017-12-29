"""Tests for investment views."""

import re
import uuid
from collections import Counter
from datetime import date, datetime
from unittest.mock import patch

import pytest
import reversion
from django.utils.timezone import now, utc
from freezegun import freeze_time
from oauth2_provider.models import Application
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import (
    APITestMixin, create_test_user, format_date_or_datetime, synchronous_executor_submit,
    synchronous_transaction_on_commit
)
from datahub.core.utils import executor
from datahub.documents.av_scan import virus_scan_document
from datahub.investment import views
from datahub.investment.models import (
    InvestmentProject, InvestmentProjectPermission, InvestmentProjectTeamMember, IProjectDocument
)
from datahub.investment.test.factories import (
    ActiveInvestmentProjectFactory, AssignPMInvestmentProjectFactory,
    InvestmentProjectFactory, InvestmentProjectTeamMemberFactory,
    VerifyWinInvestmentProjectFactory, WonInvestmentProjectFactory
)
from datahub.metadata.test.factories import TeamFactory
from datahub.oauth.scopes import Scope


class TestListView(APITestMixin):
    """
    Tests for the investment project list view.

    These cover GET /v3/investment
    """

    def test_investments_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        url = reverse('api-v3:investment:investment-collection')
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_projects_success(self):
        """Test successfully listing projects."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 1
        assert response_data['results'][0]['id'] == str(project.id)
        assert response_data['results'][0].keys() == {
            'id',
            'incomplete_fields',
            'name',
            'project_code',
            'investment_type',
            'description',
            'anonymous_description',
            'estimated_land_date',
            'actual_land_date',
            'quotable_as_public_case_study',
            'likelihood_of_landing',
            'priority',
            'approved_commitment_to_invest',
            'approved_fdi',
            'approved_good_value',
            'approved_high_value',
            'approved_landed',
            'approved_non_fdi',
            'stage',
            'status',
            'reason_delayed',
            'reason_abandoned',
            'date_abandoned',
            'reason_lost',
            'date_lost',
            'country_lost_to',
            'investor_company',
            'investor_type',
            'investor_company_country',
            'intermediate_company',
            'level_of_involvement',
            'specific_programme',
            'client_contacts',
            'client_relationship_manager',
            'client_relationship_manager_team',
            'referral_source_adviser',
            'referral_source_activity',
            'referral_source_activity_website',
            'referral_source_activity_marketing',
            'referral_source_activity_event',
            'fdi_type',
            'sector',
            'business_activities',
            'other_business_activity',
            'archived',
            'archived_on',
            'archived_reason',
            'archived_by',
            'archived_documents_url_path',
            'created_on',
            'modified_on',
            'fdi_value',
            'total_investment',
            'foreign_equity_investment',
            'government_assistance',
            'some_new_jobs',
            'number_new_jobs',
            'will_new_jobs_last_two_years',
            'average_salary',
            'number_safeguarded_jobs',
            'r_and_d_budget',
            'non_fdi_r_and_d_budget',
            'associated_non_fdi_r_and_d_project',
            'new_tech_to_uk',
            'export_revenue',
            'value_complete',
            'client_cannot_provide_total_investment',
            'client_cannot_provide_foreign_investment',
            'client_requirements',
            'site_decided',
            'address_1',
            'address_2',
            'address_town',
            'address_postcode',
            'competitor_countries',
            'uk_region_locations',
            'strategic_drivers',
            'client_considering_other_countries',
            'uk_company_decided',
            'uk_company',
            'requirements_complete',
            'project_manager',
            'project_assurance_adviser',
            'project_manager_team',
            'project_assurance_team',
            'team_complete',
            'team_members'
        }

    def test_list_is_sorted_by_created_on_desc(self):
        """Test list is sorted by created on desc."""
        datetimes = [date(year, 1, 1) for year in range(2015, 2030)]
        investment_projects = []

        for creation_datetime in datetimes:
            with freeze_time(creation_datetime):
                investment_projects.append(
                    InvestmentProjectFactory()
                )

        url = reverse('api-v3:investment:investment-collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(investment_projects)
        response_data = response.json()['results']

        investment_projects = sorted(
            investment_projects,
            key=lambda key: key.created_on,
            reverse=True
        )
        ids = [str(ip.id) for ip in investment_projects]
        assert [ip['id'] for ip in response_data] == ids

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

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.read_all,),
        (InvestmentProjectPermission.read_associated, InvestmentProjectPermission.read_all),
    ))
    def test_non_restricted_user_can_see_all_projects(self, permissions):
        """Test that normal users can see all projects."""
        team = TeamFactory()
        team_others = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)
        adviser_2 = AdviserFactory(dit_team_id=team_others.id)

        _, api_client = _create_user_and_api_client(self, team, permissions)

        iproject_1 = InvestmentProjectFactory()
        iproject_2 = InvestmentProjectFactory()

        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)
        InvestmentProjectTeamMemberFactory(adviser=adviser_2, investment_project=iproject_2)

        url = reverse('api-v3:investment:investment-collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert {str(iproject_1.pk), str(iproject_2.pk)} == {
            result['id'] for result in response_data['results']
        }

    def test_restricted_users_cannot_see_other_teams_projects(self):
        """Tests that restricted users can only see their team's projects."""
        team = TeamFactory()
        team_others = TeamFactory()
        adviser_other = AdviserFactory(dit_team_id=team_others.id)
        adviser_same_team = AdviserFactory(dit_team_id=team.id)

        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.read_associated]
        )

        project_other = InvestmentProjectFactory()
        project_1 = InvestmentProjectFactory()
        project_2 = InvestmentProjectFactory(created_by=adviser_same_team)
        project_3 = InvestmentProjectFactory(client_relationship_manager=adviser_same_team)
        project_4 = InvestmentProjectFactory(project_manager=adviser_same_team)
        project_5 = InvestmentProjectFactory(project_assurance_adviser=adviser_same_team)

        InvestmentProjectTeamMemberFactory(adviser=adviser_other, investment_project=project_other)
        InvestmentProjectTeamMemberFactory(adviser=adviser_same_team, investment_project=project_1)

        url = reverse('api-v3:investment:investment-collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5

        results = response_data['results']
        expected_ids = {str(project_1.id), str(project_2.id), str(project_3.id),
                        str(project_4.id), str(project_5.id)}

        assert {result['id'] for result in results} == expected_ids

    def test_restricted_user_with_no_team_cannot_see_projects(self):
        """
        Checks that a restricted user that doesn't have a team cannot view any projects (in
        particular projects associated with other advisers that don't have teams).
        """
        adviser_other = AdviserFactory(dit_team_id=None)
        request_user = create_test_user(
            permission_codenames=['read_associated_investmentproject']
        )
        api_client = self.create_api_client(user=request_user)

        InvestmentProjectFactory()
        InvestmentProjectFactory(created_by=adviser_other)

        url = reverse('api-v3:investment:investment-collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0


class TestCreateView(APITestMixin):
    """
    Tests for the investment project create view.

    These cover POST /v3/investment
    """

    def test_create_project_complete_success(self):
        """Test successfully creating a project."""
        contacts = [ContactFactory(), ContactFactory()]
        investor_company = CompanyFactory()
        intermediate_company = CompanyFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:investment-collection')
        aerospace_id = constants.Sector.aerospace_assembly_aircraft.value.id
        new_site_id = constants.FDIType.creation_of_new_site_or_activity.value.id
        retail_business_activity_id = constants.InvestmentBusinessActivity.retail.value.id
        other_business_activity_id = constants.InvestmentBusinessActivity.other.value.id
        activities = [{
            'id': retail_business_activity_id
        }, {
            'id': other_business_activity_id
        }]
        request_data = {
            'name': 'project name',
            'description': 'project description',
            'anonymous_description': 'project anon description',
            'estimated_land_date': '2020-12-12',
            'quotable_as_public_case_study': True,
            'likelihood_of_landing': 60,
            'priority': '1_low',
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            },
            'stage': {
                'id': constants.InvestmentProjectStage.prospect.value.id
            },
            'business_activities': activities,
            'other_business_activity': 'New innovation centre',
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
        assert response_data['anonymous_description'] == request_data['anonymous_description']
        assert response_data['estimated_land_date'] == request_data['estimated_land_date']
        assert (response_data['quotable_as_public_case_study'] ==
                request_data['quotable_as_public_case_study'])
        assert response_data['likelihood_of_landing'] == request_data['likelihood_of_landing']
        assert response_data['priority'] == request_data['priority']
        assert re.match('^DHP-\d+$', response_data['project_code'])

        assert response_data['investment_type']['id'] == request_data['investment_type']['id']
        assert response_data['investor_company']['id'] == str(investor_company.id)
        assert response_data['intermediate_company']['id'] == str(intermediate_company.id)
        assert response_data['referral_source_adviser']['id'] == str(adviser.id)
        assert response_data['stage']['id'] == request_data['stage']['id']
        assert response_data['status'] == 'ongoing'  # default status
        assert len(response_data['client_contacts']) == 2
        assert Counter(contact['id'] for contact in response_data[
            'client_contacts']) == Counter(str(contact.id) for contact in contacts)
        assert Counter(activity['id'] for activity in response_data[
            'business_activities']) == Counter(activity['id'] for activity in activities)
        assert response_data['other_business_activity'] == request_data['other_business_activity']

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

    def test_create_project_conditional_failure(self):
        """Test creating a project w/ missing conditionally required value."""
        contacts = [ContactFactory(), ContactFactory()]
        investor_company = CompanyFactory()
        intermediate_company = CompanyFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:investment-collection')
        aerospace_id = constants.Sector.aerospace_assembly_aircraft.value.id
        retail_business_activity_id = constants.InvestmentBusinessActivity.retail.value.id
        request_data = {
            'name': 'project name',
            'description': 'project description',
            'estimated_land_date': '2020-12-12',
            'investment_type': {
                'id': constants.InvestmentType.fdi.value.id
            },
            'stage': {
                'id': constants.InvestmentProjectStage.prospect.value.id
            },
            'business_activities': [{
                'id': retail_business_activity_id
            }],
            'client_contacts': [{
                'id': str(contacts[0].id)
            }, {
                'id': str(contacts[1].id)
            }],
            'client_relationship_manager': {
                'id': str(adviser.id)
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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'fdi_type': ['This field is required.']
        }


class TestRetrieveView(APITestMixin):
    """
    Tests for the investment project retrieve view.

    These cover GET /v3/investment/<id>
    """

    def test_get_project_success(self):
        """Test successfully getting a project."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['id'] == str(project.id)
        assert response_data['name'] == project.name
        assert response_data['description'] == project.description
        assert response_data['likelihood_of_landing'] == project.likelihood_of_landing
        assert response_data['project_code'] == project.project_code
        assert response_data['estimated_land_date'] == str(project.estimated_land_date)
        assert response_data['investment_type']['id'] == str(project.investment_type.id)
        assert (response_data['stage']['id'] == str(project.stage.id))
        investor_company = project.investor_company
        assert response_data['investor_company'] == {
            'id': str(investor_company.id),
            'name': investor_company.name
        }
        assert response_data['investor_company_country'] == {
            'id': str(investor_company.registered_address_country.id),
            'name': investor_company.registered_address_country.name
        }
        client_relationship_manager = project.client_relationship_manager
        assert response_data['client_relationship_manager'] == {
            'id': str(client_relationship_manager.id),
            'first_name': client_relationship_manager.first_name,
            'name': client_relationship_manager.name,
            'last_name': client_relationship_manager.last_name,
        }
        assert response_data['client_relationship_manager_team'] == {
            'id': str(client_relationship_manager.dit_team.id),
            'name': client_relationship_manager.dit_team.name
        }
        expected_client_contact_ids = sorted(
            [str(contact.id) for contact in project.client_contacts.all()]
        )
        assert sorted(contact['id'] for contact in response_data[
            'client_contacts']) == expected_client_contact_ids

    def test_get_project_no_investor_and_crm(self):
        """
        Test getting a company when investor_company and client_relationship_manager are None.
        """
        project = InvestmentProjectFactory(
            investor_company=None,
            client_relationship_manager=None,
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['id'] == str(project.id)
        assert response_data['investor_company'] is None
        assert response_data['investor_company_country'] is None
        assert response_data['client_relationship_manager'] is None
        assert response_data['client_relationship_manager_team'] is None

    def test_get_project_status(self):
        """Test getting project status fields."""
        project = InvestmentProjectFactory(
            status=InvestmentProject.STATUSES.lost,
            reason_delayed='Problems getting planning permission.',
            date_abandoned=date(2019, 1, 1),
            reason_abandoned='No longer viable.',
            reason_lost='Lower set-up costs.',
            date_lost=date(2018, 1, 1),
            country_lost_to_id=constants.Country.japan.value.id,
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['id'] == str(project.id)
        assert response_data['status'] == project.status
        assert response_data['reason_delayed'] == project.reason_delayed
        assert response_data['date_abandoned'] == project.date_abandoned.isoformat()
        assert response_data['reason_abandoned'] == project.reason_abandoned
        assert response_data['reason_lost'] == project.reason_lost
        assert response_data['date_lost'] == project.date_lost.isoformat()
        assert response_data['country_lost_to']['id'] == constants.Country.japan.value.id

    def test_get_value_success(self):
        """Test successfully getting a project value object."""
        higher_value = constants.FDIValue.higher.value
        project = InvestmentProjectFactory(
            fdi_value_id=higher_value.id,
            client_cannot_provide_foreign_investment=False,
            client_cannot_provide_total_investment=False,
            total_investment=100,
            foreign_equity_investment=100,
            government_assistance=True,
            some_new_jobs=False,
            number_new_jobs=0,
            will_new_jobs_last_two_years=False,
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
        assert response_data['fdi_value']['id'] == higher_value.id
        assert response_data['client_cannot_provide_foreign_investment'] is False
        assert response_data['client_cannot_provide_total_investment'] is False
        assert response_data['total_investment'] == '100'
        assert response_data['foreign_equity_investment'] == '100'
        assert response_data['government_assistance'] is True
        assert response_data['total_investment'] == '100'
        assert response_data['some_new_jobs'] is False
        assert response_data['number_new_jobs'] == 0
        assert response_data['will_new_jobs_last_two_years'] is False
        assert response_data['number_safeguarded_jobs'] == 10
        assert response_data['r_and_d_budget'] is False
        assert response_data['non_fdi_r_and_d_budget'] is False
        assert response_data['associated_non_fdi_r_and_d_project'] is None
        assert response_data['new_tech_to_uk'] is False
        assert response_data['export_revenue'] is True
        assert response_data['value_complete'] is True

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
            address_1='address 1',
            client_considering_other_countries=True,
            competitor_countries=countries,
            strategic_drivers=strategic_drivers,
            uk_company_decided=False,
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
        assert response_data['uk_company_decided'] is False
        assert response_data['address_1'] == 'address 1'
        assert sorted(country['id'] for country in response_data[
            'competitor_countries']) == sorted(countries)
        assert sorted(driver['id'] for driver in response_data[
            'strategic_drivers']) == sorted(strategic_drivers)

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
            'last_name': pm_adviser.last_name,
            'name': pm_adviser.name
        }
        assert response_data['project_assurance_adviser'] == {
            'id': str(pa_adviser.pk),
            'first_name': pa_adviser.first_name,
            'last_name': pa_adviser.last_name,
            'name': pa_adviser.name,
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

    def test_incomplete_fields_prospect(self):
        """Tests moving an incomplete project to the Assign PM stage."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert Counter(response_data['incomplete_fields']) == Counter((
            'client_cannot_provide_total_investment',
            'number_new_jobs',
            'total_investment',
            'client_considering_other_countries',
            'client_requirements',
            'strategic_drivers',
            'uk_region_locations',
        ))

    def test_restricted_user_cannot_see_project_if_not_associated(self):
        """Tests that a restricted user cannot view another team's project."""
        team_requester = TeamFactory()
        team_associated = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team_associated.id)

        _, api_client = _create_user_and_api_client(
            self, team_requester, [InvestmentProjectPermission.read_associated]
        )

        iproject_1 = InvestmentProjectFactory()
        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': iproject_1.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.read_all,),
        (InvestmentProjectPermission.read_associated, InvestmentProjectPermission.read_all),
    ))
    def test_non_restricted_user_can_see_project_if_not_associated(self, permissions):
        """Tests that non-restricted users can access projects they aren't associated with."""
        team_requester = TeamFactory()
        team_associated = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team_associated.id)

        _, api_client = _create_user_and_api_client(self, team_requester, permissions)

        iproject_1 = InvestmentProjectFactory()
        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': iproject_1.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_restricted_user_can_see_project_if_associated_via_team_member(self):
        """Tests that restricted users can see a project associated to them via a team member."""
        team = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.read_associated]
        )

        iproject_1 = InvestmentProjectFactory()
        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': iproject_1.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize('field', (
        'created_by',
        'client_relationship_manager',
        'project_assurance_adviser',
        'project_manager'))
    def test_restricted_user_can_see_project_if_associated_via_field(self, field):
        """Tests that restricted users can see a project when in the team of the creator."""
        team = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)

        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.read_associated]
        )

        iproject_1 = InvestmentProjectFactory(**{field: adviser_1})

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': iproject_1.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_restricted_user_with_no_team_cannot_view_project(self):
        """
        Checks that a restricted user that doesn't have a team cannot view a project created by
        another user without a team.
        """
        adviser_other = AdviserFactory(dit_team_id=None)
        request_user = create_test_user(
            permission_codenames=['read_associated_investmentproject']
        )
        api_client = self.create_api_client(user=request_user)

        project = InvestmentProjectFactory(created_by=adviser_other)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPartialUpdateView(APITestMixin):
    """
    Tests for the investment project partial update view.

    These cover PATCH /v3/investment/<id>
    """

    def test_patch_project_conditional_failure(self):
        """Test updating a project w/ missing conditionally required value."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'investment_type': {
                'id': str(constants.InvestmentType.fdi.value.id)
            },
            'fdi_type': None
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
        project = InvestmentProjectFactory()
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
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
        }

    def test_change_stage_assign_pm_success(self):
        """Tests moving a complete project to the Assign PM stage."""
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = InvestmentProjectFactory(
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
        project = InvestmentProjectFactory()
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
            'strategic_drivers': ['This field is required.'],
            'uk_region_locations': ['This field is required.'],
            'project_assurance_adviser': ['This field is required.'],
            'project_manager': ['This field is required.'],
        }

    def test_change_stage_active_success(self):
        """Tests moving a complete project to the Active stage."""
        adviser = AdviserFactory()
        project = AssignPMInvestmentProjectFactory(
            project_assurance_adviser=adviser,
            project_manager=adviser,
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
        project = ActiveInvestmentProjectFactory(number_new_jobs=1)
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
            'address_1': ['This field is required.'],
            'address_town': ['This field is required.'],
            'address_postcode': ['This field is required.'],
            'average_salary': ['This field is required.'],
            'client_cannot_provide_foreign_investment': ['This field is required.'],
            'foreign_equity_investment': ['This field is required.'],
        }

    def test_change_stage_verify_win_success(self):
        """Tests moving a complete project to the 'Verify win' stage."""
        strategic_drivers = [
            constants.InvestmentStrategicDriver.access_to_market.value.id
        ]
        project = ActiveInvestmentProjectFactory(
            client_cannot_provide_foreign_investment=False,
            foreign_equity_investment=200,
            client_requirements='client reqs',
            strategic_drivers=strategic_drivers,
            uk_region_locations=[constants.UKRegion.england.value.id],
            government_assistance=False,
            number_safeguarded_jobs=0,
            r_and_d_budget=True,
            non_fdi_r_and_d_budget=True,
            associated_non_fdi_r_and_d_project=InvestmentProjectFactory(),
            new_tech_to_uk=True,
            export_revenue=True,
            address_1='12 London Road',
            address_town='London',
            address_postcode='SW1A 2AA',
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

    def test_change_stage_to_won(self):
        """Tests moving a complete project to the 'Won' stage."""
        project = VerifyWinInvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.won.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['stage'] == {
            'id': constants.InvestmentProjectStage.won.value.id,
            'name': constants.InvestmentProjectStage.won.value.name,
        }
        assert response_data['status'] == 'won'

    def test_revert_stage_to_verify_win(self):
        """Tests moving a complete project from the 'Won' stage to 'Verify win'."""
        project = WonInvestmentProjectFactory()
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'stage': {
                'id': constants.InvestmentProjectStage.verify_win.value.id
            }
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['stage'] == {
            'id': constants.InvestmentProjectStage.verify_win.value.id,
            'name': constants.InvestmentProjectStage.verify_win.value.name,
        }
        assert response_data['status'] == 'ongoing'

    def test_invalid_state_validation(self):
        """Tests validation when a project that is in an invalid state.

        An invalid state means that fields that are required for the current stage have
        not been completed. Generally, this should be impossible as those fields should've
        been completed before moving to the current stage. Only the fields being modified
        should be validated in this state (unless the stage is being modified).
        """
        project = InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.active.value.id,
            project_manager=None
        )
        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        request_data = {
            'project_manager': None
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'project_manager': ['This field is required.'],
        }

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

    def test_patch_requirements_success(self):
        """Test successfully partially updating a requirements object."""
        project = InvestmentProjectFactory(client_requirements='client reqs',
                                           site_decided=True,
                                           address_1='address 1')
        url = reverse('api-v3:investment:investment-item',
                      kwargs={'pk': project.pk})
        request_data = {
            'address_1': 'address 1 new',
            'address_2': 'address 2 new'
        }
        response = self.api_client.patch(url, data=request_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['requirements_complete'] is False
        assert response_data['client_requirements'] == 'client reqs'
        assert response_data['site_decided'] is True
        assert response_data['address_1'] == 'address 1 new'
        assert response_data['address_2'] == 'address 2 new'

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
            'last_name': adviser_2.last_name,
            'name': adviser_2.name
        }
        assert response_data['project_assurance_adviser'] == {
            'id': str(adviser_2.pk),
            'first_name': adviser_2.first_name,
            'last_name': adviser_2.last_name,
            'name': adviser_2.name
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

    def test_update_read_only_fields(self):
        """Test updating read-only fields."""
        project = InvestmentProjectFactory(
            archived_documents_url_path='old_path',
        )

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = self.api_client.patch(url, format='json', data={
            'archived_documents_url_path': 'new_path'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived_documents_url_path'] == 'old_path'

    def test_restricted_user_cannot_update_project_if_not_associated(self):
        """Tests that a restricted user cannot update another team's project."""
        team_requester = TeamFactory()
        team_associated = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team_associated.id)

        _, api_client = _create_user_and_api_client(
            self, team_requester, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory(name='old name')
        InvestmentProjectTeamMemberFactory(adviser=adviser, investment_project=project)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = api_client.patch(url, {
            'name': 'new name'
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_all, InvestmentProjectPermission.change_associated),
    ))
    def test_non_restricted_user_can_update_project_if_not_associated(self, permissions):
        """Tests that non-restricted users can update projects they aren't associated with."""
        team_requester = TeamFactory()
        team_associated = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team_associated.id)

        _, api_client = _create_user_and_api_client(self, team_requester, permissions)

        project = InvestmentProjectFactory(name='old name')
        InvestmentProjectTeamMemberFactory(adviser=adviser, investment_project=project)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = api_client.patch(url, {
            'name': 'new name'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['name'] == 'new name'

    def test_restricted_user_can_update_project_if_associated_via_team_member(self):
        """
        Tests that restricted users can update a project associated to them via a team member.
        """
        team = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team.id)
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory(name='old name')
        InvestmentProjectTeamMemberFactory(adviser=adviser, investment_project=project)

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = api_client.patch(url, {
            'name': 'new name'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['name'] == 'new name'

    @pytest.mark.parametrize('field', (
        'created_by',
        'client_relationship_manager',
        'project_assurance_adviser',
        'project_manager'))
    def test_restricted_user_can_update_project_if_associated_via_field(self, field):
        """Tests that restricted users can update a project when in the team of the creator."""
        team = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team.id)

        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory(name='old name', **{field: adviser})

        url = reverse('api-v3:investment:investment-item', kwargs={'pk': project.pk})
        response = api_client.patch(url, {
            'name': 'new name'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['name'] == 'new name'


class TestModifiedSinceView(APITestMixin):
    """Tests for the modified-since view."""

    def _make_request(self, data=None):
        url = reverse('api-v3:investment:investment-modified-since-collection')
        client = self.create_api_client(
            scope=Scope.mi,
            grant_type=Application.GRANT_CLIENT_CREDENTIALS
        )
        return client.get(url, data=data)

    @pytest.mark.parametrize(
        'timestamp,num_results', (
            (datetime(2017, 12, 31), 5),
            (datetime(2018, 1, 1), 5),
            (datetime(2018, 1, 2), 0),
        )
    )
    def test_get_modified_since_filter(self, timestamp: datetime, num_results: int):
        """Test the that results are correctly filtered."""
        with freeze_time(datetime(2017, 1, 1)):
            InvestmentProjectFactory.create_batch(4)
        with freeze_time(datetime(2018, 1, 1)):
            InvestmentProjectFactory.create_batch(5)

        response = self._make_request({
            'modified_on__gte': timestamp.isoformat()
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == num_results

    @pytest.mark.parametrize(
        'timestamp,num_results', (
            (datetime(2016, 12, 31), 0),
            (datetime(2017, 1, 2), 4),
            (datetime(2018, 1, 2), 9),
        )
    )
    def test_get_modified_until_filter(self, timestamp: datetime, num_results: int):
        """Test the that results are correctly filtered."""
        with freeze_time(datetime(2017, 1, 1)):
            InvestmentProjectFactory.create_batch(4)
        with freeze_time(datetime(2018, 1, 1)):
            InvestmentProjectFactory.create_batch(5)

        response = self._make_request({
            'modified_on__lte': timestamp.isoformat()
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == num_results

    @pytest.mark.parametrize(
        'from_,until,num_results', (
            (datetime(2016, 12, 31), datetime(2017, 1, 3), 4),
            (datetime(2018, 1, 1), datetime(2018, 1, 2), 5),
            (datetime(2017, 1, 1), datetime(2018, 1, 1), 9),
            (datetime(2017, 3, 1), datetime(2017, 3, 2), 0),
        )
    )
    def test_get_modified_from_and_modified_until_filter(
            self, from_: datetime, until: datetime, num_results: int):
        """Test the that results are correctly filtered."""
        with freeze_time(datetime(2017, 1, 1)):
            InvestmentProjectFactory.create_batch(4)
        with freeze_time(datetime(2018, 1, 1)):
            InvestmentProjectFactory.create_batch(5)

        response = self._make_request({
            'modified_on__gte': from_.isoformat(),
            'modified_on__lte': until.isoformat()
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == num_results

    def test_get_all(self):
        """Test that all results are returned if no filter value is provided."""
        InvestmentProjectFactory.create_batch(4, modified_on=datetime(2017, 1, 1, tzinfo=utc))
        InvestmentProjectFactory.create_batch(5, modified_on=datetime(2018, 1, 1, tzinfo=utc))
        response = self._make_request()

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 9


class TestAddTeamMemberView(APITestMixin):
    """Tests for the add team member view."""

    def test_add_team_member_nonexistent_project(self):
        """Tests adding a team member to a non-existent project."""
        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': uuid.uuid4()})
        response = self.api_client.post(url, format='json', data={})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_team_member_missing_data(self):
        """Tests adding a team member to a project without specifying an adviser and role."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        response = self.api_client.post(url, format='json', data={})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'adviser': ['This field is required.'],
            'role': ['This field is required.']
        }

    def test_add_team_member_null_data(self):
        """Tests adding a team member to a project specifying a null adviser and role."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        response = self.api_client.post(url, format='json', data={
            'adviser': None,
            'role': None
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'adviser': ['This field may not be null.'],
            'role': ['This field may not be null.']
        }

    def test_add_team_member_blank_role(self):
        """Tests adding a team member to a project specifying a blank role."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        response = self.api_client.post(url, format='json', data={
            'adviser': {'id': str(adviser.pk)},
            'role': ''
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'role': ['This field may not be blank.']
        }

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_associated, InvestmentProjectPermission.change_all),
    ))
    def test_non_restricted_user_can_add_team_member(self, permissions):
        """Test that a non-restricted user can add a team member to a project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        team = TeamFactory()

        _, api_client = _create_user_and_api_client(self, team, permissions)

        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        request_data = {
            'adviser': {
                'id': str(adviser.pk)
            },
            'role': 'Sector adviser'
        }
        response = api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['adviser']['id'] == str(adviser.pk)
        assert response_data['role'] == 'Sector adviser'

    def test_restricted_user_cannot_add_team_member_to_non_associated_project(self):
        """Test that a restricted user cannot add a team member to a non-associated project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        team = TeamFactory()

        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        request_data = {
            'adviser': {
                'id': str(adviser.pk)
            },
            'role': 'Sector adviser'
        }
        response = api_client.post(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_add_team_member_to_associated_project(self):
        """Test that a restricted user can add a team member to an associated project."""
        adviser = AdviserFactory()
        creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=creator)

        _, api_client = _create_user_and_api_client(
            self, creator.dit_team, [InvestmentProjectPermission.change_associated]
        )
        url = reverse('api-v3:investment:team-member-collection',
                      kwargs={'project_pk': project.pk})
        request_data = {
            'adviser': {
                'id': str(adviser.pk)
            },
            'role': 'Sector adviser'
        }
        response = api_client.post(url, format='json', data=request_data)

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


class TestDeleteAllTeamMembersView(APITestMixin):
    """Tests for the delete all team members view."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_associated, InvestmentProjectPermission.change_all),
    ))
    def test_non_restricted_user_can_delete_all_team_members(self, permissions):
        """Test that a non-restricted user can remove all team members from a project."""
        project = InvestmentProjectFactory()
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        InvestmentProjectTeamMemberFactory()

        team = TeamFactory()
        _, api_client = _create_user_and_api_client(self, team, permissions)

        url = reverse('api-v3:investment:team-member-collection', kwargs={
            'project_pk': team_members[0].investment_project.pk
        })
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not InvestmentProjectTeamMember.objects.filter(investment_project=project).exists()
        assert InvestmentProjectTeamMember.objects.all().exists()

    def test_restricted_user_cannot_delete_all_team_members_of_non_associated_project(self):
        """
        Test that a restricted user cannot remove all team members from a non-associated project.
        """
        project = InvestmentProjectFactory()
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        InvestmentProjectTeamMemberFactory()

        team = TeamFactory()
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        url = reverse('api-v3:investment:team-member-collection', kwargs={
            'project_pk': team_members[0].investment_project.pk
        })
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_delete_all_team_members_of_associated_project(self):
        """
        Test that a restricted user can remove all team members from an associated project.
        """
        creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=creator)
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        InvestmentProjectTeamMemberFactory()

        _, api_client = _create_user_and_api_client(
            self, creator.dit_team, [InvestmentProjectPermission.change_associated]
        )

        url = reverse('api-v3:investment:team-member-collection', kwargs={
            'project_pk': team_members[0].investment_project.pk
        })
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not InvestmentProjectTeamMember.objects.filter(investment_project=project).exists()
        assert InvestmentProjectTeamMember.objects.all().exists()


class TestGetTeamMemberView(APITestMixin):
    """Tests for the get team member view."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.read_all,),
        (InvestmentProjectPermission.read_associated, InvestmentProjectPermission.read_all),
    ))
    def test_non_restricted_user_can_get_team_member(self, permissions):
        """Test that a non-restricted user can get a team member."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(self, team, permissions)
        response = api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['role'] == team_member.role

    def test_restricted_user_cannot_get_team_member_of_non_associated_project(self):
        """Test that a restricted user cannot get a team member of a non-associated project."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.read_associated]
        )
        response = api_client.get(url, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_get_team_member_of_associated_project(self):
        """Test that a restricted user can get a team member of an associated project."""
        creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=creator)
        team_member = InvestmentProjectTeamMemberFactory(investment_project=project)
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        _, api_client = _create_user_and_api_client(
            self, creator.dit_team, [InvestmentProjectPermission.read_associated]
        )
        response = api_client.get(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['role'] == team_member.role

    def test_get_team_member_nonexistent_adviser(self):
        """Tests getting a non-existent project team member."""
        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': project.pk,
            'adviser_pk': uuid.uuid4()
        })
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_team_member_nonexistent_project(self):
        """Tests getting a project team member for a non-existent project."""
        adviser = AdviserFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': uuid.uuid4(),
            'adviser_pk': adviser.pk
        })
        response = self.api_client.get(url, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateTeamMemberView(APITestMixin):
    """Tests for the update team member view."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_associated, InvestmentProjectPermission.change_all),
    ))
    def test_non_restricted_user_can_patch_team_member(self, permissions):
        """Test that a non-restricted user can update a team member."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        request_data = {
            'role': 'updated role'
        }
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(self, team, permissions)
        response = api_client.patch(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['role'] == request_data['role']

    def test_restricted_user_cannot_patch_team_member_of_non_associated_project(self):
        """Test that a restricted user cannot update a team member of a non-associated project."""
        team_member = InvestmentProjectTeamMemberFactory()
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        request_data = {
            'role': 'updated role'
        }
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )
        response = api_client.patch(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_patch_team_member_of_associated_project(self):
        """Test that a restricted user can update a team member of an associated project."""
        creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=creator)
        team_member = InvestmentProjectTeamMemberFactory(investment_project=project)
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_member.investment_project.pk,
            'adviser_pk': team_member.adviser.pk
        })
        request_data = {
            'role': 'updated role'
        }
        _, api_client = _create_user_and_api_client(
            self, creator.dit_team, [InvestmentProjectPermission.change_associated]
        )
        response = api_client.patch(url, format='json', data=request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['role'] == request_data['role']


class TestDeleteTeamMemberView(APITestMixin):
    """Tests for the delete team member views."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_associated, InvestmentProjectPermission.change_all),
    ))
    def test_non_restricted_user_can_delete_team_member(self, permissions):
        """Test that a non-restricted user can remove a team member from a project."""
        project = InvestmentProjectFactory()
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_members[0].investment_project.pk,
            'adviser_pk': team_members[0].adviser.pk
        })
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(self, team, permissions)
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        new_team_members = InvestmentProjectTeamMember.objects.filter(investment_project=project)
        assert new_team_members.count() == 1
        assert new_team_members[0].adviser.pk == team_members[1].adviser.pk

    def test_restricted_user_cannot_delete_team_member_of_non_associated_project(self):
        """
        Test that a restricted user cannot remove a team member from a project from a
        non-associated project.
        """
        project = InvestmentProjectFactory()
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_members[0].investment_project.pk,
            'adviser_pk': team_members[0].adviser.pk
        })
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_delete_team_member_of_associated_project(self):
        """
        Test that a restricted user can remove a team member from a project from an
        associated project.
        """
        creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=creator)
        team_members = InvestmentProjectTeamMemberFactory.create_batch(
            2, investment_project=project
        )
        url = reverse('api-v3:investment:team-member-item', kwargs={
            'project_pk': team_members[0].investment_project.pk,
            'adviser_pk': team_members[0].adviser.pk
        })
        _, api_client = _create_user_and_api_client(
            self, creator.dit_team, [InvestmentProjectPermission.change_associated]
        )
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        new_team_members = InvestmentProjectTeamMember.objects.filter(investment_project=project)
        assert new_team_members.count() == 1
        assert new_team_members[0].adviser.pk == team_members[1].adviser.pk


class TestAuditLogView(APITestMixin):
    """Tests for the audit log view."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.read_all,),
        (InvestmentProjectPermission.read_associated, InvestmentProjectPermission.read_all),
    ))
    def test_audit_log_non_restricted_user(self, permissions):
        """Test retrieval of audit log for a non-restricted user."""
        team = TeamFactory()
        user, api_client = _create_user_and_api_client(self, team, permissions)

        initial_datetime = now()
        with reversion.create_revision():
            iproject = InvestmentProjectFactory(
                description='Initial desc',
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(user)

        changed_datetime = now()
        with reversion.create_revision():
            iproject.description = 'New desc'
            iproject.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(user)

        versions = Version.objects.get_for_object(iproject)
        version_id = versions[0].id
        url = reverse('api-v3:investment:audit-item',
                      kwargs={'pk': iproject.pk})

        response = api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1, 'Only one entry in audit log'
        entry = response_data[0]

        assert entry['id'] == version_id
        assert entry['user']['name'] == user.name, 'Valid user captured'
        assert entry['comment'] == 'Changed', 'Comments can be set manually'
        assert entry['timestamp'] == format_date_or_datetime(changed_datetime), \
            'TS can be set manually'
        assert entry['changes']['description'] == ['Initial desc', 'New desc'], \
            'Changes are reflected'
        assert not {'created_on', 'created_by', 'modified_on', 'modified_by'} & entry[
            'changes'].keys()

    def test_audit_log_restricted_user_associated_project(self):
        """Test retrieval of audit log for a restricted user and an associated project."""
        team = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team.id)
        user, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.read_associated]
        )

        initial_datetime = now()
        with reversion.create_revision():
            iproject = InvestmentProjectFactory(
                description='Initial desc',
                created_by=adviser,
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(user)

        changed_datetime = now()
        with reversion.create_revision():
            iproject.description = 'New desc'
            iproject.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(user)

        versions = Version.objects.get_for_object(iproject)
        version_id = versions[0].id
        url = reverse('api-v3:investment:audit-item',
                      kwargs={'pk': iproject.pk})

        response = api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1, 'Only one entry in audit log'
        entry = response_data[0]

        assert entry['id'] == version_id
        assert entry['user']['name'] == user.name, 'Valid user captured'
        assert entry['comment'] == 'Changed', 'Comments can be set manually'
        assert entry['timestamp'] == format_date_or_datetime(changed_datetime), \
            'TS can be set manually'
        assert entry['changes']['description'] == ['Initial desc', 'New desc'], \
            'Changes are reflected'
        assert not {'created_on', 'created_by', 'modified_on', 'modified_by'} & entry[
            'changes'].keys()

    def test_audit_log_restricted_user_non_associated_project(self):
        """Test retrieval of audit log for a restricted user and a non-associated project."""
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.read_associated]
        )

        iproject = InvestmentProjectFactory(
            description='Initial desc',
        )
        url = reverse('api-v3:investment:audit-item', kwargs={'pk': iproject.pk})

        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestArchiveViews(APITestMixin):
    """Tests for the archive and unarchive views."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_associated, InvestmentProjectPermission.change_all),
    ))
    def test_archive_project_non_restricted_user(self, permissions):
        """Tests archiving a project for a non-restricted user."""
        team = TeamFactory()
        user, api_client = _create_user_and_api_client(self, team, permissions)

        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = api_client.post(url, format='json', data={
            'reason': 'archive reason'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is True
        assert response_data['archived_by']['id'] == str(user.pk)
        assert response_data['archived_reason'] == 'archive reason'

    def test_archive_project_restricted_user_associated_project(self):
        """Tests archiving a project for a restricted user."""
        team = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team.id)
        user, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory(created_by=adviser)
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = api_client.post(url, format='json', data={
            'reason': 'archive reason'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is True
        assert response_data['archived_by']['id'] == str(user.pk)
        assert response_data['archived_reason'] == 'archive reason'

    def test_archive_project_restricted_user_non_associated_project(self):
        """Test that a restricted user cannot archive a non-associated project."""
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory()
        url = reverse('api-v3:investment:archive-item',
                      kwargs={'pk': project.pk})
        response = api_client.post(url, format='json', data={
            'reason': 'archive reason'
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN

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

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.change_all,),
        (InvestmentProjectPermission.change_associated, InvestmentProjectPermission.change_all),
    ))
    def test_unarchive_project_non_restricted_user(self, permissions):
        """Tests unarchiving a project for a non-restricted user."""
        team = TeamFactory()
        _, api_client = _create_user_and_api_client(self, team, permissions)

        project = InvestmentProjectFactory(
            archived=True, archived_reason='reason'
        )
        url = reverse('api-v3:investment:unarchive-item',
                      kwargs={'pk': project.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is False
        assert response_data['archived_by'] is None
        assert response_data['archived_reason'] == ''

    def test_unarchive_project_restricted_user_associated_project(self):
        """Tests unarchiving a project for a restricted user and associated project."""
        team = TeamFactory()
        adviser = AdviserFactory(dit_team_id=team.id)
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory(
            archived=True,
            archived_reason='reason',
            created_by=adviser,
        )
        url = reverse('api-v3:investment:unarchive-item',
                      kwargs={'pk': project.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is False
        assert response_data['archived_by'] is None
        assert response_data['archived_reason'] == ''

    def test_unarchive_project_restricted_user_non_associated_project(self):
        """Test that a restricted user cannot unarchive a non-associated project."""
        team = TeamFactory()
        AdviserFactory(dit_team_id=team.id)
        _, api_client = _create_user_and_api_client(
            self, team, [InvestmentProjectPermission.change_associated]
        )

        project = InvestmentProjectFactory(
            archived=True,
            archived_reason='reason',
        )
        url = reverse('api-v3:investment:unarchive-item',
                      kwargs={'pk': project.pk})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDocumentViews(APITestMixin):
    """Tests for the document views."""

    def test_documents_list_is_filtered_by_project(self):
        """Tests viewset filtering."""
        project1 = InvestmentProjectFactory()
        project2 = InvestmentProjectFactory()

        IProjectDocument.create_from_declaration_request(project1, 'total_investment', 'test.txt')
        doc2 = IProjectDocument.create_from_declaration_request(
            project2, 'total_investment', 'test.txt'
        )

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
            'doc_type': 'total_investment',
            'project': str(project.pk),
        })

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.data
        assert response_data['doc_type'] == 'total_investment'
        assert response_data['filename'] == 'test.txt'
        assert response_data['project']['id'] == str(project.pk)

        doc = IProjectDocument.objects.get(pk=response_data['id'])
        assert doc.filename == 'test.txt'
        assert doc.doc_type == 'total_investment'
        assert doc.project.pk == project.pk
        assert 'signed_upload_url' in response.data

    def test_document_retrieval(self):
        """Tests retrieval of individual document."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(
            project, 'total_investment', 'test.txt'
        )

        url = reverse('api-v3:investment:document-item',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(doc.pk)
        assert response.data['project'] == {
            'id': str(project.pk),
            'name': project.name,
        }
        assert response.data['doc_type'] == 'total_investment'
        assert response.data['filename'] == 'test.txt'
        assert 'signed_url' in response.data

    @patch.object(executor, 'submit')
    def test_document_upload_status(self, mock_submit):
        """Tests setting of document upload status to complete.

        Checks that a virus scan of the document was scheduled. Virus scanning is
        tested separately in the documents app.
        """
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(
            project, 'total_investment', 'test.txt'
        )

        url = reverse('api-v3:investment:document-item-callback',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.post(url, format='json', data={
            'status': 'success'
        })
        assert response.status_code == status.HTTP_200_OK
        mock_submit.assert_called_once_with(virus_scan_document, str(doc.pk))

    @patch.object(executor, 'submit')
    @patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_document_delete_of_not_uploaded_doc_does_not_trigger_s3_delete(self, mock_submit):
        """Tests document deletion."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(
            project, 'total_investment', 'test.txt'
        )

        url = reverse('api-v3:investment:document-item',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mock_submit.called is False

    @patch('datahub.core.utils.get_s3_client')
    @patch('datahub.core.utils.executor.submit', synchronous_executor_submit)
    @patch('django.db.transaction.on_commit', synchronous_transaction_on_commit)
    def test_document_delete(self, mock_s3):
        """Tests document deletion."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(
            project, 'total_investment', 'test.txt'
        )
        doc.document.uploaded_on = now()
        doc.document.save()

        url = reverse('api-v3:investment:document-item',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_s3().delete_object.assert_called_with(
            Bucket=doc.document.s3_bucket,
            Key=doc.document.s3_key,
        )

    def test_document_upload_status_wrong_status(self):
        """Tests request validation in the document status endpoint."""
        project = InvestmentProjectFactory()
        doc = IProjectDocument.create_from_declaration_request(
            project, 'total_investment', 'test.txt'
        )

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
        doc = IProjectDocument.create_from_declaration_request(
            project, 'total_investment', 'test.txt'
        )

        url = reverse('api-v3:investment:document-item-callback',
                      kwargs={'project_pk': project.pk, 'doc_pk': doc.pk})

        response = self.api_client.post(url, format='json', data={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.json()


@pytest.mark.parametrize('view_set', (views.IProjectAuditViewSet,))
def test_view_set_name(view_set):
    """Test that the view name is a string."""
    assert isinstance(view_set().get_view_name(), str)


def _create_user_and_api_client(test_instance, team, permissions):
    user = create_test_user(dit_team=team, permission_codenames=permissions)
    api_client = test_instance.create_api_client(user=user)
    return user, api_client
