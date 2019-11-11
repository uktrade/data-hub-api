import datetime
from cgi import parse_header
from collections import Counter
from csv import DictReader
from decimal import Decimal
from io import StringIO
from unittest import mock
from uuid import UUID

import factory
import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import OneListTier
from datahub.company.test.factories import AdviserFactory, CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_csv_data,
    get_attr_or_none,
    join_attr_values,
    random_obj_for_queryset,
)
from datahub.investment.project.constants import Involvement, LikelihoodToLand
from datahub.investment.project.models import InvestmentProject, InvestmentProjectPermission
from datahub.investment.project.test.factories import (
    GVAMultiplierFactory,
    InvestmentProjectFactory,
    InvestmentProjectTeamMemberFactory,
    VerifyWinInvestmentProjectFactory,
    WonInvestmentProjectFactory,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import TeamFactory
from datahub.search.investment import InvestmentSearchApp
from datahub.search.investment.views import SearchInvestmentExportAPIView

pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.es_collector_apps.with_args(InvestmentSearchApp),
]


@pytest.fixture
def project_with_max_gross_value_added():
    """Test fixture returns an investment project with the max gross value."""
    gva_multiplier = GVAMultiplierFactory(
        multiplier=Decimal('9.999999'),
        financial_year=1980,
    )

    with mock.patch(
        'datahub.investment.project.gva_utils.GrossValueAddedCalculator._get_gva_multiplier',
    ) as mock_get_multiplier:
        mock_get_multiplier.return_value = gva_multiplier
        project = InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            name='won project',
            description='investmentproject3',
            estimated_land_date=datetime.date(2027, 9, 13),
            actual_land_date=datetime.date(2022, 11, 13),
            investor_company=CompanyFactory(
                address_country_id=constants.Country.united_kingdom.value.id,
            ),
            project_manager=AdviserFactory(),
            project_assurance_adviser=AdviserFactory(),
            fdi_value_id=constants.FDIValue.higher.value.id,
            status=InvestmentProject.STATUSES.won,
            uk_region_locations=[
                constants.UKRegion.north_west.value.id,
            ],
            level_of_involvement_id=Involvement.hq_only.value.id,
            likelihood_to_land_id=None,
            foreign_equity_investment=9999999999999999999,
        )
    return project


@pytest.fixture
def setup_data(es_with_collector, project_with_max_gross_value_added):
    """Sets up data for the tests."""
    investment_projects = [
        InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            name='abc defg',
            description='investmentproject1',
            estimated_land_date=datetime.date(2011, 6, 13),
            actual_land_date=datetime.date(2010, 8, 13),
            investor_company=CompanyFactory(
                address_country_id=constants.Country.united_states.value.id,
            ),
            status=InvestmentProject.STATUSES.ongoing,
            uk_region_locations=[
                constants.UKRegion.east_midlands.value.id,
                constants.UKRegion.isle_of_man.value.id,
            ],
            level_of_involvement_id=Involvement.hq_and_post_only.value.id,
            likelihood_to_land_id=LikelihoodToLand.high.value.id,
            foreign_equity_investment=100000,
        ),
        InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            name='delayed project',
            description='investmentproject2',
            estimated_land_date=datetime.date(2057, 6, 13),
            actual_land_date=datetime.date(2047, 8, 13),
            country_investment_originates_from_id=constants.Country.ireland.value.id,
            investor_company=CompanyFactory(
                address_country_id=constants.Country.japan.value.id,
            ),
            project_manager=AdviserFactory(),
            project_assurance_adviser=AdviserFactory(),
            fdi_value_id=constants.FDIValue.higher.value.id,
            status=InvestmentProject.STATUSES.delayed,
            uk_region_locations=[
                constants.UKRegion.north_west.value.id,
            ],
            level_of_involvement_id=Involvement.no_involvement.value.id,
            likelihood_to_land_id=LikelihoodToLand.medium.value.id,
        ),
        project_with_max_gross_value_added,
        InvestmentProjectFactory(
            name='new project',
            description='investmentproject4',
            country_investment_originates_from_id=constants.Country.canada.value.id,
            estimated_land_date=None,
            level_of_involvement_id=None,
            likelihood_to_land_id=LikelihoodToLand.low.value.id,
        ),
    ]
    es_with_collector.flush_and_refresh()

    yield investment_projects


@pytest.fixture
def created_on_data(es_with_collector):
    """Setup data for created_on date filter test."""
    investment_projects = []
    dates = (
        '2015-01-01', '2016-09-12', '2017-09-12', '2048-02-04', '2048-01-24',
    )

    for date in dates:
        with freeze_time(date):
            investment_projects.append(
                InvestmentProjectFactory(),
            )

    es_with_collector.flush_and_refresh()

    yield investment_projects


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_search_investment_project_json(self, setup_data):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'original_query': 'abc defg',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'abc defg'

    @pytest.mark.parametrize(
        'search,expected_gross_value_added,expected_project_name',
        (
            (
                {
                    'gross_value_added_start': 99999999999999,
                },
                ['99999989999999999991'],
                ['won project'],
            ),
            (
                {
                    'gross_value_added_end': 99999999999999,
                },
                ['5810'],
                ['abc defg'],
            ),
            (
                {
                    'gross_value_added_start': 0,
                    'gross_value_added_end': 6000,
                },
                ['5810'],
                ['abc defg'],
            ),
            (
                {
                    'gross_value_added_start': 20000000000000000000000,
                },
                [],
                [],
            ),
        ),
    )
    def test_gross_value_added_filters(
        self,
        setup_data,
        search,
        expected_gross_value_added,
        expected_project_name,
    ):
        """Test Gross Value Added (GVA) filters."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data=search,
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            Counter(
                str(Decimal(result['gross_value_added'])) for result in response.data['results']
            ) == Counter(expected_gross_value_added)
        ), expected_gross_value_added
        assert (
            Counter(result['name'] for result in response.data['results'])
            == Counter(expected_project_name)
        ), expected_project_name

    def test_search_adviser_filter(self, es_with_collector):
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

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'adviser': adviser.pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 6
        results = response_data['results']
        expected_ids = {
            str(project_1.pk), str(project_2.pk), str(project_3.pk),
            str(project_4.pk), str(project_5.pk), str(project_6.pk),
        }
        assert {result['id'] for result in results} == expected_ids

    @pytest.mark.parametrize(
        'query,num_results',
        (
            (
                {
                    'estimated_land_date_before': '2017-06-13',
                },
                1,
            ),
            (
                {
                    'estimated_land_date_after': '2017-06-13',
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
        ),
    )
    def test_search_investment_project_estimated_land_date_json(
        self,
        setup_data,
        query,
        num_results,
    ):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, query)

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
                    'actual_land_date_before': '2010-12-13',
                },
                [
                    'abc defg',
                ],
            ),
            (
                {
                    'actual_land_date_before': '2022-11-13',
                },
                [
                    'abc defg',
                    'won project',
                ],
            ),
            (
                {
                    'actual_land_date_after': '2010-12-13',
                },
                [
                    'delayed project',
                    'won project',
                ],
            ),
            (
                {
                    'actual_land_date_after': '2022-11-13',
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
        ),
    )
    def test_search_investment_project_actual_land_date_json(
        self,
        setup_data,
        query,
        expected_results,
    ):
        """Tests the actual land date filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, query)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_results)
        results = response.data['results']
        assert Counter(result['name'] for result in results) == Counter(expected_results)

    @pytest.mark.parametrize(
        'query,num_results',
        (
            (
                {
                    'created_on_before': '2016-09-13T09:44:31.062870Z',
                },
                2,
            ),
            (
                {
                    'created_on_before': '2016-09-12T00:00:00.000000Z',
                },
                2,
            ),
            (
                {
                    'created_on_after': '2017-06-13T09:44:31.062870Z',
                },
                3,
            ),
            (
                {
                    'created_on_after': '2016-09-12T00:00:00.000000Z',
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
        ),
    )
    def test_search_investment_project_created_on_json(self, created_on_data, query, num_results):
        """Tests detailed investment project search."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(url, query)

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

        response = self.api_client.post(
            url,
            data={
                'estimated_land_date_before': 'this is definitely not a valid date',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'estimated_land_date_before': ['Date is in incorrect format.']}

    def test_search_investment_project_status(self, setup_data):
        """Tests investment project search status filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'status': ['delayed', 'won'],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        statuses = {result['status'] for result in response.data['results']}
        assert statuses == {'delayed', 'won'}

    def test_search_investment_project_investor_country(self, setup_data):
        """Tests investor company country filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'investor_company_country': constants.Country.japan.value.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'delayed project'

    def test_search_investment_project_investor_country_when_investment_origin_set(
        self, setup_data,
    ):
        """Tests investor company country filter when investment origin also set."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'investor_company_country': constants.Country.ireland.value.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'delayed project'

    def test_search_investment_project_investment_origin(
        self, setup_data,
    ):
        """Tests country investment originates from filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'country_investment_originates_from': constants.Country.canada.value.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'new project'

    @pytest.mark.parametrize(
        'query,expected_results',
        (
            (
                {
                    'level_of_involvement_simplified': 'unspecified',
                },
                [
                    'new project',
                ],
            ),
            (
                {
                    'level_of_involvement_simplified': ['unspecified', 'involved'],
                },
                [
                    'new project',
                    'abc defg',
                    'won project',
                ],
            ),
            (
                {
                    'level_of_involvement_simplified': ['not_involved', 'involved'],
                },
                [
                    'abc defg',
                    'delayed project',
                    'won project',
                ],
            ),
            (
                {
                    'level_of_involvement_simplified': 'involved',
                },
                [
                    'abc defg',
                    'won project',
                ],
            ),
            (
                {
                    'level_of_involvement_simplified': 'not_involved',
                },
                [
                    'delayed project',
                ],
            ),
            (
                {
                    'level_of_involvement_simplified': ['unspecified', 'not_involved'],
                },
                [
                    'new project',
                    'delayed project',
                ],
            ),
            (
                {
                    'likelihood_to_land': LikelihoodToLand.low.value.id,
                },
                [
                    'new project',
                ],
            ),
            (
                {
                    'likelihood_to_land': [
                        LikelihoodToLand.low.value.id,
                        LikelihoodToLand.medium.value.id,
                    ],
                },
                [
                    'new project', 'delayed project',
                ],
            ),
            (
                {
                },
                [
                    'abc defg',
                    'delayed project',
                    'won project',
                    'new project',
                ],
            ),
        ),
    )
    def test_search_involvement_json(
        self,
        setup_data,
        query,
        expected_results,
    ):
        """Tests the involvement filter."""
        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, query)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == len(expected_results)
        results = response.data['results']
        assert Counter(result['name'] for result in results) == Counter(expected_results)

    @pytest.mark.parametrize(
        'query,expected_error',
        (
            (
                {
                    'level_of_involvement_simplified': 'unspecified1',
                },
                {
                    'level_of_involvement_simplified': ['"unspecified1" is not a valid choice.'],
                },
            ),
            (
                {
                    'level_of_involvement_simplified': ['unspecified5', 'great_involvement'],
                },
                {
                    'level_of_involvement_simplified': {
                        '0': ['"unspecified5" is not a valid choice.'],
                        '1': ['"great_involvement" is not a valid choice.'],
                    },
                },
            ),
            (
                {
                    'level_of_involvement_simplified': ['not_involved', 'great_involvement'],
                },
                {
                    'level_of_involvement_simplified': {
                        '1': ['"great_involvement" is not a valid choice.'],
                    },
                },
            ),
        ),
    )
    def test_search_involvement_incorrect_filter_json(
        self,
        setup_data,
        query,
        expected_error,
    ):
        """Tests that involvement filter won't work with incorrect filter value."""
        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, query)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_search_investment_project_uk_region_location(self, setup_data):
        """Tests uk_region_location filter."""
        url = reverse('api-v3:search:investment_project')

        response = self.api_client.post(
            url,
            data={
                'uk_region_location': constants.UKRegion.east_midlands.value.id,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'abc defg'

    @pytest.mark.parametrize(
        'sector_level',
        (0, 1, 2),
    )
    def test_sector_descends_filter(self, hierarchical_sectors, es_with_collector, sector_level):
        """Test the sector_descends filter."""
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        projects = InvestmentProjectFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )
        InvestmentProjectFactory.create_batch(
            3,
            sector=factory.LazyFunction(lambda: random_obj_for_queryset(
                Sector.objects.exclude(pk__in=sectors_ids),
            )),
        )

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:investment_project')
        body = {
            'sector_descends': hierarchical_sectors[sector_level].pk,
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == num_sectors - sector_level

        actual_ids = {UUID(project['id']) for project in response_data['results']}
        expected_ids = {project.pk for project in projects[sector_level:]}
        assert actual_ids == expected_ids

    def test_search_investment_project_no_filters(self, setup_data):
        """Tests case where there is no filters provided."""
        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_investment_project_multiple_filters(self, es_with_collector):
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
            stage_id=constants.InvestmentProjectStage.active.value.id,
        )
        investment_project2 = InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )

        InvestmentProjectFactory(
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )
        InvestmentProjectFactory(
            investment_type_id=constants.InvestmentType.fdi.value.id,
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )

        es_with_collector.flush_and_refresh()

        response = self.api_client.post(
            url,
            data={
                'investment_type': constants.InvestmentType.fdi.value.id,
                'investor_company': [
                    investment_project1.investor_company.pk,
                    investment_project2.investor_company.pk,
                ],
                'stage': [
                    constants.InvestmentProjectStage.won.value.id,
                    constants.InvestmentProjectStage.active.value.id,
                ],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

        # checks if we only have investment projects with stages we filtered
        assert {
            constants.InvestmentProjectStage.active.value.id,
            constants.InvestmentProjectStage.won.value.id,
        } == {
            investment_project['stage']['id']
            for investment_project in response.data['results']
        }

        # checks if we only have investment projects with investor companies we filtered
        assert {
            str(investment_project1.investor_company.pk),
            str(investment_project2.investor_company.pk),
        } == {
            investment_project['investor_company']['id']
            for investment_project in response.data['results']
        }

        # checks if we only have investment projects with fdi investment type
        assert {
            constants.InvestmentType.fdi.value.id,
        } == {
            investment_project['investment_type']['id']
            for investment_project in response.data['results']
        }

    def test_search_sort_nested_desc(self, es_with_collector, setup_data):
        """Tests sorting by nested field."""
        InvestmentProjectFactory(
            name='Potato 1',
            stage_id=constants.InvestmentProjectStage.active.value.id,
        )
        InvestmentProjectFactory(
            name='Potato 2',
            stage_id=constants.InvestmentProjectStage.prospect.value.id,
        )
        InvestmentProjectFactory(
            name='potato 3',
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )
        InvestmentProjectFactory(
            name='Potato 4',
            stage_id=constants.InvestmentProjectStage.won.value.id,
        )

        es_with_collector.flush_and_refresh()

        term = 'Potato'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'stage.name:desc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert [
            'Won',
            'Won',
            'Prospect',
            'Active',
        ] == [
            investment_project['stage']['name'] for investment_project in response.data['results']
        ]


class TestSearchPermissions(APITestMixin):
    """Tests search view permissions."""

    def test_investment_project_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:investment_project')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'permissions',
        (
            (InvestmentProjectPermission.view_all,),
            (InvestmentProjectPermission.view_associated, InvestmentProjectPermission.view_all),
        ),
    )
    def test_non_restricted_user_can_see_all_projects(self, es_with_collector, permissions):
        """Test that normal users can see all projects."""
        team = TeamFactory()
        team_others = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)
        adviser_2 = AdviserFactory(dit_team_id=team_others.id)

        request_user = create_test_user(
            permission_codenames=permissions,
            dit_team=team,
        )
        api_client = self.create_api_client(user=request_user)

        iproject_1 = InvestmentProjectFactory()
        iproject_2 = InvestmentProjectFactory()

        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)
        InvestmentProjectTeamMemberFactory(adviser=adviser_2, investment_project=iproject_2)

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:investment_project')
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert {str(iproject_1.pk), str(iproject_2.pk)} == {
            result['id'] for result in response_data['results']
        }

    def test_restricted_user_with_no_team_cannot_see_projects(self, es_with_collector):
        """
        Checks that a restricted user that doesn't have a team cannot view any projects (in
        particular projects associated with other advisers that don't have teams).
        """
        url = reverse('api-v3:search:investment_project')

        adviser_other = AdviserFactory(dit_team_id=None)
        request_user = create_test_user(
            permission_codenames=['view_associated_investmentproject'],
        )
        api_client = self.create_api_client(user=request_user)

        InvestmentProjectFactory()
        InvestmentProjectFactory(created_by=adviser_other)

        es_with_collector.flush_and_refresh()

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0

    def test_restricted_users_cannot_see_other_teams_projects(self, es_with_collector):
        """Test that restricted users cannot see other teams' projects."""
        url = reverse('api-v3:search:investment_project')

        team = TeamFactory()
        team_other = TeamFactory()
        adviser_other = AdviserFactory(dit_team_id=team_other.id)
        adviser_same_team = AdviserFactory(dit_team_id=team.id)
        request_user = create_test_user(
            permission_codenames=['view_associated_investmentproject'],
            dit_team=team,
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

        es_with_collector.flush_and_refresh()

        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5

        results = response_data['results']
        expected_ids = {
            str(project_1.id), str(project_2.id), str(project_3.id),
            str(project_4.id), str(project_5.id),
        }

        assert {result['id'] for result in results} == expected_ids


class TestInvestmentProjectExportView(APITestMixin):
    """Tests the investment project export view."""

    @pytest.mark.parametrize(
        'permissions',
        (
            (),
            (InvestmentProjectPermission.view_all,),
            (InvestmentProjectPermission.export,),
        ),
    )
    def test_user_without_permission_cannot_export(self, es, permissions):
        """Test that a user without the correct permissions cannot export data."""
        user = create_test_user(dit_team=TeamFactory(), permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:investment_project-export')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_users_cannot_see_other_teams_projects(self, es_with_collector):
        """Test that restricted users cannot see other teams' projects in the export."""
        team = TeamFactory()
        team_other = TeamFactory()
        adviser_other = AdviserFactory(dit_team_id=team_other.id)
        adviser_same_team = AdviserFactory(dit_team_id=team.id)
        request_user = create_test_user(
            permission_codenames=(
                InvestmentProjectPermission.view_associated,
                InvestmentProjectPermission.export,
            ),
            dit_team=team,
        )
        api_client = self.create_api_client(user=request_user)

        project_other = InvestmentProjectFactory()
        team_projects = [
            InvestmentProjectFactory(),
            InvestmentProjectFactory(created_by=adviser_same_team),
            InvestmentProjectFactory(client_relationship_manager=adviser_same_team),
            InvestmentProjectFactory(project_manager=adviser_same_team),
            InvestmentProjectFactory(project_assurance_adviser=adviser_same_team),
        ]

        InvestmentProjectTeamMemberFactory(adviser=adviser_other, investment_project=project_other)
        InvestmentProjectTeamMemberFactory(
            adviser=adviser_same_team,
            investment_project=team_projects[0],
        )

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:investment_project-export')
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK

        response_text = response.getvalue().decode('utf-8-sig')
        reader = DictReader(StringIO(response_text))
        actual_rows = [dict(item) for item in reader]

        assert len(actual_rows) == 5

        expected_names = {project.name for project in team_projects}

        assert {row['Project name'] for row in actual_rows} == expected_names

    def _get_global_account_manager_name(self, project):
        gam = project.investor_company.get_one_list_group_global_account_manager()
        return get_attr_or_none(gam, 'name')

    @pytest.mark.parametrize(
        'request_sortby,orm_ordering',
        (
            ('created_on:desc', '-created_on'),
            ('stage.name', 'stage__name'),
        ),
    )
    def test_export(self, es_with_collector, request_sortby, orm_ordering):
        """Test export of investment project search results."""
        url = reverse('api-v3:search:investment_project-export')

        InvestmentProjectFactory()
        InvestmentProjectFactory(cdms_project_code='cdms-code')
        VerifyWinInvestmentProjectFactory()
        won_project = WonInvestmentProjectFactory()
        InvestmentProjectTeamMemberFactory.create_batch(3, investment_project=won_project)

        InvestmentProjectFactory(
            name='project for subsidiary',
            investor_company=CompanyFactory(
                global_headquarters=CompanyFactory(
                    one_list_tier_id=OneListTier.objects.first().id,
                    one_list_account_owner=AdviserFactory(),
                ),
            ),
        )

        es_with_collector.flush_and_refresh()

        data = {}
        if request_sortby:
            data['sortby'] = request_sortby

        with freeze_time('2018-01-01 11:12:13'):
            response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {'filename': 'Data Hub - Investment projects - 2018-01-01-11-12-13.csv'},
        )

        sorted_projects = InvestmentProject.objects.order_by(orm_ordering, 'pk')
        response_text = response.getvalue().decode('utf-8-sig')
        reader = DictReader(StringIO(response_text))

        assert reader.fieldnames == list(SearchInvestmentExportAPIView.field_titles.values())

        # E123 is ignored as there are seemingly unresolvable indentation errors in the dict below
        expected_row_data = [  # noqa: E123
            {
                'Date created': project.created_on,
                'Project reference': project.project_code,
                'Project name': project.name,
                'Investor company': project.investor_company.name,
                'Investor company town or city': project.investor_company.address_town,
                'Country of origin':
                    get_attr_or_none(project, 'investor_company.address_country.name'),
                'Investment type': get_attr_or_none(project, 'investment_type.name'),
                'Status': project.get_status_display(),
                'Stage': get_attr_or_none(project, 'stage.name'),
                'Link':
                    f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["investmentproject"]}'
                    f'/{project.pk}',
                'Actual land date': project.actual_land_date,
                'Estimated land date': project.estimated_land_date,
                'FDI value': get_attr_or_none(project, 'fdi_value.name'),
                'Sector': get_attr_or_none(project, 'sector.name'),
                'Date of latest interaction': None,
                'Project manager': get_attr_or_none(project, 'project_manager.name'),
                'Client relationship manager':
                    get_attr_or_none(project, 'client_relationship_manager.name'),
                'Global account manager': self._get_global_account_manager_name(project),
                'Project assurance adviser':
                    get_attr_or_none(project, 'project_assurance_adviser.name'),
                'Other team members':
                    join_attr_values(
                        project.team_members.order_by('adviser__first_name', 'adviser__last_name'),
                        'adviser.name',
                    ),
                'Delivery partners':
                    join_attr_values(
                        project.delivery_partners.order_by('name'),
                    ),
                'Possible UK regions':
                    join_attr_values(
                        project.uk_region_locations.order_by('name'),
                    ),
                'Actual UK regions':
                    join_attr_values(
                        project.actual_uk_regions.order_by('name'),
                    ),
                'Specific investment programme':
                    get_attr_or_none(project, 'specific_programme.name'),
                'Referral source activity':
                    get_attr_or_none(project, 'referral_source_activity.name'),
                'Referral source activity website':
                    get_attr_or_none(project, 'referral_source_activity_website.name'),
                'Total investment': project.total_investment,
                'New jobs': project.number_new_jobs,
                'Average salary of new jobs': get_attr_or_none(project, 'average_salary.name'),
                'Safeguarded jobs': project.number_safeguarded_jobs,
                'Level of involvement': get_attr_or_none(project, 'level_of_involvement.name'),
                'Likelihood to land': get_attr_or_none(project, 'likelihood_to_land.name'),
                'R&D budget': project.r_and_d_budget,
                'Associated non-FDI R&D project': project.non_fdi_r_and_d_budget,
                'New to world tech': project.new_tech_to_uk,
                'FDI type': project.fdi_type,
                'Foreign equity investment': project.foreign_equity_investment,
                'GVA multiplier': get_attr_or_none(project, 'gva_multiplier.multiplier'),
                'GVA': project.gross_value_added,
            }
            for project in sorted_projects
        ]

        expected_rows = format_csv_data(expected_row_data)

        # item is an ordered dict so is cast to a dict to make the comparison easier to
        # interpret in the event of the assert actual_rows == expected_rows failing.
        actual_rows = [dict(item) for item in reader]

        assert actual_rows == expected_rows


class TestBasicSearch(APITestMixin):
    """Tests basic search view."""

    def test_investment_projects(self, setup_data):
        """Tests basic aggregate investment project query."""
        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'investment_project',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == term
        assert [{'count': 1, 'entity': 'investment_project'}] == response.data['aggregations']

    def test_project_code_search(self, setup_data):
        """Tests basic search query for project code."""
        investment_project = setup_data[0]

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': investment_project.project_code,
                'entity': 'investment_project',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['project_code'] == investment_project.project_code


class TestBasicSearchPermissions(APITestMixin):
    """Tests basic search view permissions."""

    @pytest.mark.parametrize(
        'permissions',
        (
            (InvestmentProjectPermission.view_all,),
            (InvestmentProjectPermission.view_associated, InvestmentProjectPermission.view_all),
        ),
    )
    def test_global_non_restricted_user_can_see_all_projects(self, es_with_collector, permissions):
        """Test that normal users can see all projects."""
        team = TeamFactory()
        team_others = TeamFactory()
        adviser_1 = AdviserFactory(dit_team_id=team.id)
        adviser_2 = AdviserFactory(dit_team_id=team_others.id)

        request_user = create_test_user(
            permission_codenames=permissions,
            dit_team=team,
        )
        api_client = self.create_api_client(user=request_user)

        iproject_1 = InvestmentProjectFactory()
        iproject_2 = InvestmentProjectFactory()

        InvestmentProjectTeamMemberFactory(adviser=adviser_1, investment_project=iproject_1)
        InvestmentProjectTeamMemberFactory(adviser=adviser_2, investment_project=iproject_2)

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(
            url,
            data={
                'term': '',
                'entity': 'investment_project',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert {str(iproject_1.pk), str(iproject_2.pk)} == {
            result['id'] for result in response_data['results']
        }

    def test_global_restricted_users_cannot_see_other_teams_projects(self, es_with_collector):
        """
        Automatic filter to see only associated IP for a specific (leps) user
        """
        team = TeamFactory()
        team_other = TeamFactory()
        adviser_other = AdviserFactory(dit_team_id=team_other.id)
        adviser_same_team = AdviserFactory(dit_team_id=team.id)
        request_user = create_test_user(
            permission_codenames=['view_associated_investmentproject'],
            dit_team=team,
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

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(
            url,
            data={
                'term': '',
                'entity': 'investment_project',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5

        results = response_data['results']
        expected_ids = {
            str(project_1.id), str(project_2.id), str(project_3.id),
            str(project_4.id), str(project_5.id),
        }

        assert {result['id'] for result in results} == expected_ids

    def test_global_restricted_user_with_no_team_cannot_see_projects(self, es_with_collector):
        """
        Checks that a restricted user that doesn't have a team cannot view projects associated
        with other advisers that don't have teams.
        """
        adviser_other = AdviserFactory(dit_team_id=None)
        request_user = create_test_user(
            permission_codenames=['view_associated_investmentproject'],
        )
        api_client = self.create_api_client(user=request_user)

        InvestmentProjectFactory()
        InvestmentProjectFactory(created_by=adviser_other)

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(
            url,
            data={
                'term': '',
                'entity': 'investment_project',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0
