import datetime
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.investment.models import InvestmentProject
from datahub.investment.test.factories import InvestmentProjectFactory
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


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_investment_project_no_permissions(self):
        """Should return 403"""
        user = create_test_user(team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:investment_project')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

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

    def test_search_investment_project_date_json(self, setup_data):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, {
            'estimated_land_date_before': datetime.datetime(2017, 6, 13, 9, 44, 31, 62870),
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1

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
