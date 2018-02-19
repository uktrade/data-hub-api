import datetime
from collections import Counter

import pytest
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.investment.models import InvestmentProject, InvestmentProjectPermission
from datahub.investment.test.factories import (
    InvestmentProjectFactory, InvestmentProjectTeamMemberFactory
)
from datahub.metadata.test.factories import TeamFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(setup_es):
    """Sets up data for the tests."""
    investment_projects = [
        InvestmentProjectFactory(
            name='abc defg',
            description='investmentproject1',
            estimated_land_date=datetime.date(2011, 6, 13),
            actual_land_date=datetime.date(2010, 8, 13),
            investor_company=CompanyFactory(
                registered_address_country_id=constants.Country.united_states.value.id
            ),
            status=InvestmentProject.STATUSES.ongoing,
            uk_region_locations=[
                constants.UKRegion.east_midlands.value.id,
                constants.UKRegion.isle_of_man.value.id,
            ],
        ),
        InvestmentProjectFactory(
            name='delayed project',
            description='investmentproject2',
            estimated_land_date=datetime.date(2057, 6, 13),
            actual_land_date=datetime.date(2047, 8, 13),
            investor_company=CompanyFactory(
                registered_address_country_id=constants.Country.japan.value.id
            ),
            project_manager=AdviserFactory(),
            project_assurance_adviser=AdviserFactory(),
            fdi_value_id=constants.FDIValue.higher.value.id,
            status=InvestmentProject.STATUSES.delayed,
            uk_region_locations=[
                constants.UKRegion.north_west.value.id,
            ],
        ),
        InvestmentProjectFactory(
            name='won project',
            description='investmentproject3',
            estimated_land_date=datetime.date(2027, 9, 13),
            actual_land_date=datetime.date(2022, 11, 13),
            investor_company=CompanyFactory(
                registered_address_country_id=constants.Country.united_kingdom.value.id
            ),
            project_manager=AdviserFactory(),
            project_assurance_adviser=AdviserFactory(),
            fdi_value_id=constants.FDIValue.higher.value.id,
            status=InvestmentProject.STATUSES.won,
            uk_region_locations=[
                constants.UKRegion.north_west.value.id,
            ],
        )
    ]
    setup_es.indices.refresh()

    yield investment_projects


@pytest.fixture
def created_on_data(setup_es):
    """Setup data for created_on date filter test."""
    investment_projects = []
    dates = (
        '2015-01-01', '2016-09-12', '2017-09-12', '2048-02-04', '2048-01-24',
    )

    for date in dates:
        with freeze_time(date):
            investment_projects.append(
                InvestmentProjectFactory()
            )

    setup_es.indices.refresh()

    yield investment_projects


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_search_investment_project_json(self, setup_data):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'original_query': 'abc defg',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'abc defg'

    def test_search_adviser_filter(self, setup_es):
        """Tests the adviser filter."""
        adviser = AdviserFactory()

        # Non-matching projects
        project_other_1 = InvestmentProjectFactory()
        InvestmentProjectTeamMemberFactory(investment_project=project_other_1)
        InvestmentProjectTeamMemberFactory(investment_project=project_other_1)
        InvestmentProjectFactory()

        # Matching projects
        project_1 = InvestmentProjectFactory()
        InvestmentProjectTeamMemberFactory(adviser=adviser, investment_project=project_1)
        InvestmentProjectTeamMemberFactory(investment_project=project_1)

        project_2 = InvestmentProjectFactory(created_by=adviser)
        project_3 = InvestmentProjectFactory(client_relationship_manager=adviser)
        project_4 = InvestmentProjectFactory(project_manager=adviser)
        project_5 = InvestmentProjectFactory(project_assurance_adviser=adviser)
        # Should only be returned once
        project_6 = InvestmentProjectFactory(
            created_by=adviser,
            client_relationship_manager=adviser,
            project_assurance_adviser=adviser,
            project_manager=adviser,
        )
        InvestmentProjectTeamMemberFactory(adviser=adviser, investment_project=project_6)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'adviser': adviser.pk,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 6
        results = response_data['results']
        expected_ids = {str(project_1.pk), str(project_2.pk), str(project_3.pk),
                        str(project_4.pk), str(project_5.pk), str(project_6.pk)}
        assert {result['id'] for result in results} == expected_ids

    @pytest.mark.parametrize(
        'query,num_results',
        (
            (
                {
                    'estimated_land_date_before': '2017-06-13'
                },
                1,
            ),
            (
                {
                    'estimated_land_date_after': '2017-06-13'
                },
                2,
            ),
            (
                {
                    'estimated_land_date_after': '2017-06-13',
                    'estimated_land_date_before': '2030-06-13',
                },
                1,
            ),
            (
                {
                    'estimated_land_date_before': '2017-06-13',
                    'estimated_land_date_after': '2030-06-13',
                },
                0,
            ),
        )
    )
    def test_search_investment_project_estimated_land_date_json(
        self,
        setup_data,
        query,
        num_results
    ):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, query, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == num_results
        results = response.data['results']
        assert len(results) == num_results

        for result in results:
            estimated_land_date = dateutil_parse(result['estimated_land_date'])
            for filter_key, date in query.items():
                date = dateutil_parse(date)
                if filter_key == 'estimated_land_date_before':
                    assert estimated_land_date <= date
                if filter_key == 'estimated_land_date_after':
                    assert estimated_land_date >= date

    @pytest.mark.parametrize(
        'query,expected_results',
        (
            (
                {
                    'actual_land_date_before': '2010-12-13'
                },
                [
                    'abc defg',
                ],
            ),
            (
                {
                    'actual_land_date_before': '2022-11-13'
                },
                [
                    'abc defg',
                    'won project',
                ],
            ),
            (
                {
                    'actual_land_date_after': '2010-12-13'
                },
                [
                    'delayed project',
                    'won project',
                ],
            ),
            (
                {
                    'actual_land_date_after': '2022-11-13'
                },
                [
                    'delayed project',
                    'won project',
                ],
            ),
            (
                {
                    'actual_land_date_after': '2010-12-13',
                    'actual_land_date_before': '2025-06-13',
                },
                [
                    'won project',
                ],
            ),
            (
                {
                    'actual_land_date_before': '2010-12-13',
                    'actual_land_date_after': '2025-06-13',
                },
                [],
            ),
        )
    )
    def test_search_investment_project_actual_land_date_json(
        self,
        setup_data,
        query,
        expected_results,
    ):
        """Tests the actual land date filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, query, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_results)
        results = response.data['results']
        assert Counter(result['name'] for result in results) == Counter(expected_results)

    @pytest.mark.parametrize(
        'query,num_results', (
            (
                {
                    'created_on_before': '2016-09-13T09:44:31.062870Z'
                },
                2,
            ),
            (
                {
                    'created_on_before': '2016-09-12T00:00:00.000000Z'
                },
                2,
            ),
            (
                {
                    'created_on_after': '2017-06-13T09:44:31.062870Z'
                },
                3,
            ),
            (
                {
                    'created_on_after': '2016-09-12T00:00:00.000000Z'
                },
                4,
            ),
            (
                {
                    'created_on_after': '2017-06-13T09:44:31.062870Z',
                    'created_on_before': '2048-02-01T05:44:31.062870Z',
                },
                2,
            ),
            (
                {
                    'created_on_before': '2017-06-13T09:44:31.062870Z',
                    'created_on_after': '2048-02-01T05:44:31.062870Z',
                },
                0,
            ),
        )
    )
    def test_search_investment_project_created_on_json(self, created_on_data, query, num_results):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, query, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == num_results
        results = response.data['results']
        assert len(results) == num_results

        for result in results:
            created_on = dateutil_parse(result['created_on']).replace(tzinfo=utc)
            for filter_key, date in query.items():
                date = dateutil_parse(date)
                if filter_key == 'created_on_before':
                    assert created_on <= date
                if filter_key == 'created_on_after':
                    assert created_on >= date

    def test_search_investment_project_invalid_date_json(self, setup_data):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'estimated_land_date_before': 'this is definitely not a valid date',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_investment_project_status(self, setup_data):
        """Tests investment project search status filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'status': ['delayed', 'won'],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        statuses = {result['status'] for result in response.data['results']}
        assert statuses == {'delayed', 'won'}

    def test_search_investment_project_investor_country(self, setup_data):
        """Tests investor company country filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'investor_company_country': constants.Country.japan.value.id,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'delayed project'

    def test_search_investment_project_uk_region_location(self, setup_data):
        """Tests uk_region_location filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'uk_region_location': constants.UKRegion.east_midlands.value.id,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'abc defg'

    def test_search_investment_project_no_filters(self, setup_data):
        """Tests case where there is no filters provided."""
        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_investment_project_multiple_filters(self, setup_es):
        """Tests multiple filters in investment project search.
        We make sure that out of provided investment projects, we will
        receive only those that match our filter.

        We are testing following filter:

        investment_type = fdi
        AND (investor_company = compA OR investor_company = compB)
        AND (stage = won OR stage = active)
        """
        url = reverse('api-v3:search:investment_project')
        investment_project1 = InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.active.value.id
        )
        investment_project2 = InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )

        InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.won.value.id
        )
        InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )

        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'investment_type': constants.InvestmentType.fdi.value.id,
            'investor_company': [
                investment_project1.investor_company.pk,
                investment_project2.investor_company.pk,
            ],
            'stage': [
                constants.InvestmentProjectStage.won.value.id,
                constants.InvestmentProjectStage.active.value.id,
            ],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

        # checks if we only have investment projects with stages we filtered
        assert {
            constants.InvestmentProjectStage.active.value.id,
            constants.InvestmentProjectStage.won.value.id
        } == {
            investment_project['stage']['id']
            for investment_project in response.data['results']
        }

        # checks if we only have investment projects with investor companies we filtered
        assert {
            str(investment_project1.investor_company.pk),
            str(investment_project2.investor_company.pk)
        } == {
            investment_project['investor_company']['id']
            for investment_project in response.data['results']
        }

        # checks if we only have investment projects with fdi investment type
        assert {
            constants.InvestmentType.fdi.value.id
        } == {
            investment_project['investment_type']['id']
            for investment_project in response.data['results']
        }

    def test_search_investment_project_aggregates(self, setup_es):
        """Tests aggregates in investment project search."""
        url = reverse('api-v3:search:investment_project')

        InvestmentProjectFactory(
            name='Pear 1',
            stage_id=constants.InvestmentProjectStage.active.value.id
        )
        InvestmentProjectFactory(
            name='Pear 2',
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )
        InvestmentProjectFactory(
            name='Pear 3',
            stage_id=constants.InvestmentProjectStage.prospect.value.id
        )
        InvestmentProjectFactory(
            name='Pear 4',
            stage_id=constants.InvestmentProjectStage.won.value.id
        )

        setup_es.indices.refresh()

        response = self.api_client.post(url, {
            'original_query': 'Pear',
            'stage': [
                constants.InvestmentProjectStage.prospect.value.id,
                constants.InvestmentProjectStage.active.value.id,
            ],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3
        assert len(response.data['results']) == 3
        assert 'aggregations' in response.data

        stages = [{'key': constants.InvestmentProjectStage.prospect.value.id, 'doc_count': 2},
                  {'key': constants.InvestmentProjectStage.active.value.id, 'doc_count': 1},
                  {'key': constants.InvestmentProjectStage.won.value.id, 'doc_count': 1}]
        assert all(stage in response.data['aggregations']['stage'] for stage in stages)


class TestSearchPermissions(APITestMixin):
    """Tests search view permissions."""

    def test_investment_project_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:investment_project')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.read_all,),
        (InvestmentProjectPermission.read_associated, InvestmentProjectPermission.read_all),
    ))
    def test_non_restricted_user_can_see_all_projects(self, setup_es, permissions):
        """Test that normal users can see all projects."""
        team = TeamFactory()
        team_others = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)
        adviser_2 = AdviserFactory(dit_team_id=team_others.id)

        request_user = create_test_user(
            permission_codenames=permissions,
            dit_team=team
        )
        api_client = self.create_api_client(user=request_user)

        iproject_1 = InvestmentProjectFactory()
        iproject_2 = InvestmentProjectFactory()

        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)
        InvestmentProjectTeamMemberFactory(adviser=adviser_2, investment_project=iproject_2)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:investment_project')
        response = api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert {str(iproject_1.pk), str(iproject_2.pk)} == {
            result['id'] for result in response_data['results']
        }

    def test_restricted_user_with_no_team_cannot_see_projects(self, setup_es):
        """
        Checks that a restricted user that doesn't have a team cannot view any projects (in
        particular projects associated with other advisers that don't have teams).
        """
        url = reverse('api-v3:search:investment_project')

        adviser_other = AdviserFactory(dit_team_id=None)
        request_user = create_test_user(
            permission_codenames=['read_associated_investmentproject']
        )
        api_client = self.create_api_client(user=request_user)

        InvestmentProjectFactory()
        InvestmentProjectFactory(created_by=adviser_other)

        setup_es.indices.refresh()

        response = api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0

    def test_restricted_users_cannot_see_other_teams_projects(self, setup_es):
        """Test that restricted users cannot see other teams' projects."""
        url = reverse('api-v3:search:investment_project')

        team = TeamFactory()
        team_other = TeamFactory()
        adviser_other = AdviserFactory(dit_team_id=team_other.id)
        adviser_same_team = AdviserFactory(dit_team_id=team.id)
        request_user = create_test_user(
            permission_codenames=['read_associated_investmentproject'],
            dit_team=team
        )
        api_client = self.create_api_client(user=request_user)

        project_other = InvestmentProjectFactory()
        project_1 = InvestmentProjectFactory()
        project_2 = InvestmentProjectFactory(created_by=adviser_same_team)
        project_3 = InvestmentProjectFactory(client_relationship_manager=adviser_same_team)
        project_4 = InvestmentProjectFactory(project_manager=adviser_same_team)
        project_5 = InvestmentProjectFactory(project_assurance_adviser=adviser_same_team)

        InvestmentProjectTeamMemberFactory(adviser=adviser_other, investment_project=project_other)
        InvestmentProjectTeamMemberFactory(adviser=adviser_same_team, investment_project=project_1)

        setup_es.indices.refresh()

        response = api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5

        results = response_data['results']
        expected_ids = {str(project_1.id), str(project_2.id), str(project_3.id),
                        str(project_4.id), str(project_5.id)}

        assert {result['id'] for result in results} == expected_ids


class TestBasicSearch(APITestMixin):
    """Tests basic search view."""

    def test_investment_projects(self, setup_data):
        """Tests basic aggregate investment project query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == term
        assert [{'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_project_code_search(self, setup_data):
        """Tests basic search query for project code."""
        investment_project = setup_data[0]

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': investment_project.project_code,
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['project_code'] == investment_project.project_code


class TestBasicSearchPermissions(APITestMixin):
    """Tests basic search view permissions."""

    @pytest.mark.parametrize('permissions', (
        (InvestmentProjectPermission.read_all,),
        (InvestmentProjectPermission.read_associated, InvestmentProjectPermission.read_all),
    ))
    def test_global_non_restricted_user_can_see_all_projects(self, setup_es, permissions):
        """Test that normal users can see all projects."""
        team = TeamFactory()
        team_others = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)
        adviser_2 = AdviserFactory(dit_team_id=team_others.id)

        request_user = create_test_user(
            permission_codenames=permissions,
            dit_team=team
        )
        api_client = self.create_api_client(user=request_user)

        iproject_1 = InvestmentProjectFactory()
        iproject_2 = InvestmentProjectFactory()

        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)
        InvestmentProjectTeamMemberFactory(adviser=adviser_2, investment_project=iproject_2)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(url, data={
            'term': '',
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert {str(iproject_1.pk), str(iproject_2.pk)} == {
            result['id'] for result in response_data['results']
        }

    def test_global_restricted_users_cannot_see_other_teams_projects(self, setup_es):
        """
        Automatic filter to see only associated IP for a specific (leps) user
        """
        team = TeamFactory()
        team_other = TeamFactory()
        adviser_other = AdviserFactory(dit_team_id=team_other.id)
        adviser_same_team = AdviserFactory(dit_team_id=team.id)
        request_user = create_test_user(
            permission_codenames=['read_associated_investmentproject'],
            dit_team=team
        )
        api_client = self.create_api_client(user=request_user)

        project_other = InvestmentProjectFactory()
        project_1 = InvestmentProjectFactory()
        project_2 = InvestmentProjectFactory(created_by=adviser_same_team)
        project_3 = InvestmentProjectFactory(client_relationship_manager=adviser_same_team)
        project_4 = InvestmentProjectFactory(project_manager=adviser_same_team)
        project_5 = InvestmentProjectFactory(project_assurance_adviser=adviser_same_team)

        InvestmentProjectTeamMemberFactory(adviser=adviser_other, investment_project=project_other)
        InvestmentProjectTeamMemberFactory(adviser=adviser_same_team, investment_project=project_1)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(url, data={
            'term': '',
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5

        results = response_data['results']
        expected_ids = {str(project_1.id), str(project_2.id), str(project_3.id),
                        str(project_4.id), str(project_5.id)}

        assert {result['id'] for result in results} == expected_ids

    def test_global_restricted_user_with_no_team_cannot_see_projects(self, setup_es):
        """
        Checks that a restricted user that doesn't have a team cannot view projects associated
        with other advisers that don't have teams.
        """
        adviser_other = AdviserFactory(dit_team_id=None)
        request_user = create_test_user(
            permission_codenames=['read_associated_investmentproject']
        )
        api_client = self.create_api_client(user=request_user)

        InvestmentProjectFactory()
        InvestmentProjectFactory(created_by=adviser_other)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(url, data={
            'term': '',
            'entity': 'investment_project'
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0
