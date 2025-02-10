from collections import Counter
from datetime import datetime, timezone
from unittest import mock

import factory
import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    SubsidiaryFactory,
)
from datahub.company_activity.models import CompanyActivity
from datahub.company_activity.tests.factories import (
    CompanyActivityEYBLeadFactory,
    CompanyActivityInteractionFactory,
    CompanyActivityInvestmentProjectFactory,
    CompanyActivityOmisOrderFactory,
    CompanyActivityReferralFactory,
)
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
)
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionDITParticipantFactory,
)
from datahub.metadata.test.factories import TeamFactory
from datahub.search.company_activity import CompanyActivitySearchApp


pytestmark = [
    pytest.mark.django_db,
    # Index objects for this search app only
    pytest.mark.opensearch_collector_apps.with_args(CompanyActivitySearchApp),
]


@pytest.fixture
def company_activities(opensearch_with_collector):
    """Sets up data for the tests."""
    data = []
    with freeze_time('2017-01-01 13:00:00'):
        company_1 = CompanyFactory(name='ABC Trading Ltd')
        company_2 = CompanyFactory(name='Little Puddle Ltd')
        data.extend(
            [
                CompanyActivityInteractionFactory(company=company_1),
                CompanyActivityInteractionFactory(company=company_1),
                CompanyActivityInteractionFactory(company=company_2),
                CompanyActivityReferralFactory(company=company_1),
                CompanyActivityReferralFactory(company=company_1),
                CompanyActivityReferralFactory(company=company_2),
                CompanyActivityReferralFactory(company=company_2),
                CompanyActivityInvestmentProjectFactory(company=company_1),
                CompanyActivityInvestmentProjectFactory(company=company_1),
                CompanyActivityInvestmentProjectFactory(company=company_2),
                CompanyActivityOmisOrderFactory(company=company_1),
                CompanyActivityOmisOrderFactory(company=company_1),
                CompanyActivityOmisOrderFactory(company=company_2),
                CompanyActivityEYBLeadFactory(company=company_1),
                CompanyActivityEYBLeadFactory(company=company_1),
                CompanyActivityEYBLeadFactory(company=company_2),
            ],
        )

    opensearch_with_collector.flush_and_refresh()

    yield data


class TestCompanyActivityEntitySearchView(APITestMixin):
    """Tests company-activity search views."""

    def test_company_activity_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:search:company-activity')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_all(self, company_activities):
        """
        Tests that all company activities are returned with an empty POST body.
        """
        url = reverse('api-v4:search:company-activity')

        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(company_activities)
        expected_ids = Counter(str(activity.id)
                               for activity in company_activities)
        assert (
            Counter([item['id']
                    for item in response_data['results']]) == expected_ids
        )

    def test_limit(self, company_activities):
        """Tests that results can be limited."""
        url = reverse('api-v4:search:company-activity')

        request_data = {
            'limit': 1,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 1

    def test_offset(self, company_activities):
        """Tests that results can be offset."""
        url = reverse('api-v4:search:company-activity')

        request_data = {
            'offset': 1,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['results']) == 15

    def test_default_sort_by_date(self, opensearch_with_collector):
        """Tests default sorting of results by date (descending)."""
        url = reverse('api-v4:search:company-activity')

        dates = (
            datetime(2017, 2, 4, 13, 15, 0, tzinfo=timezone.utc),
            datetime(2017, 1, 4, 11, 23, 10, tzinfo=timezone.utc),
            datetime(2017, 9, 29, 3, 25, 15, tzinfo=timezone.utc),
            datetime(2017, 7, 5, 11, 44, 33, tzinfo=timezone.utc),
            datetime(2017, 2, 1, 18, 15, 1, tzinfo=timezone.utc),
        )
        CompanyInteractionFactory.create_batch(
            len(dates),
            date=factory.Iterator(dates),
        )
        opensearch_with_collector.flush_and_refresh()

        response = self.api_client.post(url, {'sortby': 'date:desc'})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        sorted_dates = sorted(dates, reverse=True)
        expected_dates = [d.isoformat() for d in sorted_dates]
        assert response_data['count'] == len(dates)
        assert [item['date']
                for item in response_data['results']] == expected_dates

    @pytest.mark.parametrize(
        'sortby,error',
        (
            ('date:backwards', '"backwards" is not a valid sort direction.'),
            ('gyratory:asc', '"gyratory" is not a valid choice for the sort field.'),
        ),
    )
    def test_sort_by_invalid_field(self, opensearch_with_collector, sortby, error):
        """Tests attempting to sort by an invalid field and direction."""
        url = reverse('api-v4:search:company-activity')

        request_data = {
            'sortby': sortby,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'sortby': [error],
        }

    def test_search_dit_participant_by_id(self, opensearch_with_collector):
        """Tests dit_participants id search."""
        CompanyInteractionFactory()
        adviser_1 = AdviserFactory()
        adviser_2 = AdviserFactory()
        CompanyInteractionFactory(
            dit_participants=[
                InteractionDITParticipantFactory(adviser=adviser_1),
                InteractionDITParticipantFactory(adviser=adviser_2),
            ],
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:company-activity')

        response = self.api_client.post(
            url,
            data={
                'dit_participants__adviser': [adviser_1.id, adviser_2.id],
            },
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data['count'] == 1

    def test_filter_by_company_id(self, opensearch_with_collector):
        """Tests filtering company activities by company id."""
        companies = CompanyFactory.create_batch(10)
        CompanyInteractionFactory.create_batch(
            len(companies),
            company=factory.Iterator(companies),
        )
        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:company-activity')
        request_data = {
            'company': companies[5].id,
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data['count'] == 1

        results = response_data['results']
        assert results[0]['company']['id'] == str(companies[5].id)

    @pytest.mark.parametrize(
        'name_term,matched_company_name',
        (
            # name
            ('whiskers', 'whiskers and tabby'),
            ('whi', 'whiskers and tabby'),
            ('his', 'whiskers and tabby'),
            ('ers', 'whiskers and tabby'),
            ('1a', '1a'),
            # non-matches
            ('whi lorem', None),
            ('wh', None),
        ),
    )
    def test_filter_by_company_name(
        self,
        opensearch_with_collector,
        name_term,
        matched_company_name,
    ):
        """Tests filtering activities by company name."""
        matching_company1 = CompanyFactory(
            name='whiskers and tabby',
            trading_names=['Maine Coon', 'Egyptian Mau'],
        )
        matching_company2 = CompanyFactory(
            name='1a',
            trading_names=['3a', '4a'],
        )
        non_matching_company = CompanyFactory(
            name='Pluto and pippo',
            trading_names=['eniam nooc', 'naitpyge uam'],
        )
        CompanyInteractionFactory(company=matching_company1)
        CompanyInteractionFactory(company=matching_company2)
        CompanyInteractionFactory(company=non_matching_company)

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:company-activity')

        response = self.api_client.post(
            url,
            data={
                'original_query': '',
                'company_name': name_term,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        match = CompanyActivity.objects.filter(
            company__name=matched_company_name,
        ).first()
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(match.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    @pytest.mark.parametrize(
        'data,results',
        (
            (
                {
                    'date_after': '2017-12-01',
                },
                {
                    'talking about cats',
                    'Event at HQ',
                },
            ),
            (
                {
                    'date_after': '2017-12-01',
                    'date_before': '2018-01-02',
                },
                {
                    'Event at HQ',
                },
            ),
            (
                {
                    'date_before': '2017-01-01',
                },
                {
                    'Email about exhibition',
                },
            ),
        ),
    )
    def test_filter_by_date(self, opensearch_with_collector, data, results):
        """Tests filtering activities by date."""
        CompanyInteractionFactory(
            date=dateutil_parse('2017-10-30T00:00:00Z'),
            subject='Exports meeting',
        )
        CompanyInteractionFactory(
            date=dateutil_parse('2017-04-05T00:00:00Z'),
            subject='a coffee',
        )
        CompanyInteractionFactory(
            date=dateutil_parse('2016-09-02T00:00:00Z'),
            subject='Email about exhibition',
        )
        CompanyInteractionFactory(
            date=dateutil_parse('2018-02-01T00:00:00Z'),
            subject='talking about cats',
        )
        CompanyInteractionFactory(
            date=dateutil_parse('2018-01-01T00:00:00Z'),
            subject='Event at HQ',
        )

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:company-activity')
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        names = {
            result['interaction']['subject'] for result in response_data['results']
        }
        assert names == results

    @mock.patch(
        'datahub.search.company_activity.views.get_datahub_ids_for_dnb_service_company_hierarchy',
    )
    def test_view__include_parent_companies__includes_parent_companies_in_response(
        self,
        get_datahub_ids_dnb_service_company_hierarchy_mock,
        opensearch_with_collector,
    ):
        """
        Tests that when the following parameters are given, a company and its parent
        company activities are shown.
        ```
            company
            include_parent_companies
        ```
        """
        # Dummy companies with parent companies.
        SubsidiaryFactory.create_batch(4)

        # Test data setup
        parent_company = CompanyFactory()
        parent_company_activity_1 = CompanyInteractionFactory(
            company=parent_company,
        )
        CompanyInteractionFactory(company=parent_company)
        company = SubsidiaryFactory(global_headquarters=parent_company)
        CompanyInteractionFactory(company=company)

        opensearch_with_collector.flush_and_refresh()

        # Mocked as uses another service: dnb-service
        get_datahub_ids_dnb_service_company_hierarchy_mock.return_value = {
            'related_companies': [
                parent_company_activity_1.company_id,
            ],
            'reduced_tree': False,
        }

        url = reverse('api-v4:search:company-activity')
        request_data = {
            'company': company.id,
            'include_parent_companies': True,
        }
        response = self.api_client.post(url, request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == (
            parent_company.activities.count() + company.activities.count()
        )

    @mock.patch(
        'datahub.search.company_activity.views.get_datahub_ids_for_dnb_service_company_hierarchy',
    )
    def test_view__include_subsidiary_companies__includes_subsidiary_companies_in_response(
        self,
        get_datahub_ids_dnb_service_company_hierarchy_mock,
        opensearch_with_collector,
    ):
        """
        Tests that when the following parameters are given, a company and its subsidiary
        company activities are shown.
        ```
            company
            include_subsidiary_companies
        ```
        """
        # Dummy companies with parent companies.
        SubsidiaryFactory.create_batch(4)

        # Test data setup
        parent_company = CompanyFactory()
        parent_company_activity_1 = CompanyInteractionFactory(
            company=parent_company,
        )
        CompanyInteractionFactory(company=parent_company)
        company = SubsidiaryFactory(global_headquarters=parent_company)
        CompanyInteractionFactory(company=company)

        opensearch_with_collector.flush_and_refresh()

        # Mocked as uses another service: dnb-service
        get_datahub_ids_dnb_service_company_hierarchy_mock.return_value = {
            'related_companies': [
                parent_company_activity_1.company_id,
            ],
            'reduced_tree': False,
        }

        url = reverse('api-v4:search:company-activity')
        request_data = {
            'company': company.id,
            'include_subsidiary_companies': True,
        }
        response = self.api_client.post(url, request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == (
            parent_company.activities.count() + company.activities.count()
        )


    @pytest.mark.parametrize(
        'subject_term,matched_interaction_subject',
        (
            # interaction subject
            ('Touch', 'Touch point interaction'),
            ('Have', 'Have another go'),
            # non-matches
            ('Blah', None),
        ),
    )
    def test_filter_by_company_interaction_subject(
        self,
        opensearch_with_collector,
        subject_term,
        matched_interaction_subject,
    ):
        """Tests filtering activities by company interaction subject."""
        company = CompanyFactory()

        CompanyInteractionFactory(company=company, subject='Touch point interaction')
        CompanyInteractionFactory(company=company, subject='Have another go')
        CompanyInteractionFactory(company=company, subject='Some dummy data in here')

        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v4:search:company-activity')

        response = self.api_client.post(
            url,
            data={
                'original_query': '',
                'subject': subject_term,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        match = CompanyActivity.objects.filter(
            interaction__subject=matched_interaction_subject,
        ).first()
        
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(match.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    
    def test_sort_by_interaction_subject(self, opensearch_with_collector):
        """Tests sorting of results by interaction subject A-Z"""
        url = reverse('api-v4:search:company-activity')

        company = CompanyFactory()

        interactions = [
            CompanyInteractionFactory(company=company, subject='Touch point interaction'),
            CompanyInteractionFactory(company=company, subject='Have another go'),
            CompanyInteractionFactory(company=company, subject='Some dummy data in here'),
        ]

        opensearch_with_collector.flush_and_refresh()

        response = self.api_client.post(url, {'sortby': 'subject'})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        # Extract subjects directly from the interaction objects and sort them
        sorted_subjects = sorted(interaction.subject for interaction in interactions)

        assert response_data['count'] == len(interactions)

        # Assert the sorted subjects in the response match the expected sorted subjects
        assert [item['interaction']['subject'] for item in response_data['results']] == sorted_subjects

