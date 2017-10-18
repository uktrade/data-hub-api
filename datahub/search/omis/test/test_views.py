import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import OrderAssigneeFactory, OrderFactory, \
    OrderSubscriberFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(setup_es):
    """Sets up data for the tests."""
    with freeze_time('2017-01-01 13:00:00'):
        company = CompanyFactory(name='Mercury trading')
        contact = ContactFactory(company=company, first_name='John', last_name='Doe')
        order = OrderFactory(
            reference='ref1',
            primary_market_id=constants.Country.japan.value.id,
            assignees=[],
            status=OrderStatus.draft,
            company=company,
            contact=contact,
            discount_value=0
        )
        OrderSubscriberFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.healthcare_uk.value.id)
        )
        OrderAssigneeFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.tees_valley_lep.value.id),
            estimated_time=60
        )

    with freeze_time('2017-02-01 13:00:00'):
        company = CompanyFactory(name='Venus Ltd')
        contact = ContactFactory(company=company, first_name='Jenny', last_name='Cakeman')
        order = OrderFactory(
            reference='ref2',
            primary_market_id=constants.Country.france.value.id,
            assignees=[],
            status=OrderStatus.quote_awaiting_acceptance,
            company=company,
            contact=contact,
            discount_value=0
        )
        OrderSubscriberFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.td_events_healthcare.value.id)
        )
        OrderAssigneeFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.food_from_britain.value.id),
            estimated_time=120
        )

        setup_es.indices.refresh()


class TestSearchOrder(APITestMixin):
    """Test specific search for orders."""

    @pytest.mark.parametrize(
        'data,results',
        (
            (  # no filter => return all records
                {},
                ['ref2', 'ref1']
            ),
            (  # pagination
                {'limit': 1, 'offset': 1},
                ['ref1']
            ),
            (  # filter by primary market
                {'primary_market': constants.Country.france.value.id},
                ['ref2']
            ),
            (  # invalid market => no results
                {'primary_market': 'invalid'},
                []
            ),
            (  # filter by a range of date for created_on
                {
                    'created_on_before': '2017-02-02',
                    'created_on_after': '2017-02-01'
                },
                ['ref2']
            ),
            (  # filter by created_on_before only
                {'created_on_before': '2017-01-15'},
                ['ref1']
            ),
            (  # filter by created_on_after only
                {'created_on_after': '2017-01-15'},
                ['ref2']
            ),
            (  # filter by status
                {'status': 'quote_awaiting_acceptance'},
                ['ref2']
            ),
            (  # invalid status => no results
                {'status': 'invalid'},
                []
            ),
            (  # search by reference
                {'original_query': 'ref2'},
                ['ref2']
            ),
            (  # search by contact name exact
                {'original_query': 'Jenny Cakeman'},
                ['ref2']
            ),
            (  # search by contact name partial
                {'original_query': 'Jenny Cakem'},
                ['ref2']
            ),
            (  # search by company name exact
                {'original_query': 'Venus Ltd'},
                ['ref2']
            ),
            (  # search by company name partial
                {'original_query': 'Venus'},
                ['ref2']
            ),
            (  # search by total_cost
                {'original_query': '2000'},
                ['ref2']
            ),
            (  # search by reference
                {'reference': 'ref2'},
                ['ref2']
            ),
            (  # search by reference
                {'total_cost': 2000},
                ['ref2']
            ),
            (  # search by contact name exact
                {'contact_name': 'Jenny Cakeman'},
                ['ref2']
            ),
            (  # search by contact name partial
                {'contact_name': 'Jenny Cakem'},
                ['ref2']
            ),
            (  # search by company name exact
                {'company_name': 'Venus Ltd'},
                ['ref2']
            ),
            (  # search by company name partial
                {'company_name': 'Venus'},
                ['ref2']
            ),
        )
    )
    def test_search(self, setup_data, data, results):
        """Test search results."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == len(results)
        assert [
            item['reference'] for item in response.json()['results']
        ] == results

    def test_incorrect_dates_raise_validation_error(self, setup_data):
        """Test that if the dates are not in a valid format, the API return a validation error."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'created_on_before': 'invalid',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'non_field_errors': 'Date(s) in incorrect format.'}

    def test_filter_by_assigned_to_assignee_adviser(self, setup_data):
        """Test that results can be filtered by assignee."""
        assignee = Order.objects.get(reference='ref2').assignees.first()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'assigned_to_adviser': assignee.adviser.pk
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'ref2'

    def test_filter_by_assigned_to_assignee_adviser_team(self, setup_data):
        """Test that results can be filtered by the assignee's team."""
        assignee = Order.objects.get(reference='ref2').assignees.first()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'assigned_to_team': assignee.adviser.dit_team.pk
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'ref2'


class TestGlobalSearch(APITestMixin):
    """Test global search for orders."""

    @pytest.mark.parametrize(
        'term,results',
        (
            (  # no filter => return all records
                '',
                ['ref1', 'ref2']
            ),
            (  # search by reference
                'ref2',
                ['ref2']
            ),
            (  # search by contact name exact
                'Jenny Cakeman',
                ['ref2']
            ),
            (  # search by contact name partial
                'Jenny Cakem',
                ['ref2']
            ),
            (  # search by company name exact
                'Venus Ltd',
                ['ref2']
            ),
            (  # search by company name partial
                'Venus',
                ['ref2']
            ),
            (  # search by total_cost
                '2000',
                ['ref2']
            ),
        )
    )
    def test_search(self, setup_data, term, results):
        """Test search results."""
        url = reverse('api-v3:search:basic')

        response = self.api_client.get(url, {
            'term': term,
            'sortby': 'created_on:asc',
            'entity': 'order'
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == len(results)
        assert [
            item['reference'] for item in response.json()['results']
        ] == results
