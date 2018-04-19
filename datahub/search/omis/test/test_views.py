import pytest
from dateutil.parser import parse as dateutil_parse
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order
from datahub.omis.order.test.factories import (
    OrderAssigneeFactory, OrderFactory,
    OrderSubscriberFactory, OrderWithAcceptedQuoteFactory
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(setup_es):
    """Sets up data for the tests."""
    with freeze_time('2017-01-01 13:00:00'):
        company = CompanyFactory(name='Mercury trading', alias='Uranus supplies')
        contact = ContactFactory(company=company, first_name='John', last_name='Doe')
        order = OrderFactory(
            reference='abcd',
            primary_market_id=constants.Country.japan.value.id,
            uk_region_id=constants.UKRegion.channel_islands.value.id,
            assignees=[],
            status=OrderStatus.draft,
            company=company,
            contact=contact,
            discount_value=0,
            delivery_date=dateutil_parse('2018-01-01').date(),
            vat_verified=False
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
        company = CompanyFactory(name='Venus Ltd', alias='Earth outsourcing')
        contact = ContactFactory(company=company, first_name='Jenny', last_name='Cakeman')
        order = OrderWithAcceptedQuoteFactory(
            reference='efgh',
            primary_market_id=constants.Country.france.value.id,
            uk_region_id=constants.UKRegion.east_midlands.value.id,
            assignees=[],
            status=OrderStatus.quote_awaiting_acceptance,
            company=company,
            contact=contact,
            discount_value=0,
            delivery_date=dateutil_parse('2018-02-01').date(),
            vat_verified=False
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

    def test_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:order')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'data,results',
        (
            (  # no filter => return all records
                {},
                ['efgh', 'abcd']
            ),
            (  # pagination
                {'limit': 1, 'offset': 1},
                ['abcd']
            ),
            (  # filter by primary market
                {'primary_market': constants.Country.france.value.id},
                ['efgh']
            ),
            (  # filter by uk region
                {'uk_region': constants.UKRegion.east_midlands.value.id},
                ['efgh']
            ),
            (  # filter by a range of date for created_on
                {
                    'created_on_before': '2017-02-02',
                    'created_on_after': '2017-02-01'
                },
                ['efgh']
            ),
            (  # filter by created_on_before only
                {'created_on_before': '2017-01-15'},
                ['abcd']
            ),
            (  # filter by created_on_after only
                {'created_on_after': '2017-01-15'},
                ['efgh']
            ),
            (  # filter by status
                {'status': 'quote_awaiting_acceptance'},
                ['efgh']
            ),
            (  # invalid status => no results
                {'status': 'invalid'},
                []
            ),
            (  # search by reference
                {'original_query': 'efgh'},
                ['efgh']
            ),
            (  # search by reference partial
                {'original_query': 'efg'},
                ['efgh']
            ),
            (  # search by contact name exact
                {'original_query': 'Jenny Cakeman'},
                ['efgh']
            ),
            (  # search by contact name partial
                {'original_query': 'Jenny Cakem'},
                ['efgh']
            ),
            (  # search by company name exact
                {'original_query': 'Venus Ltd'},
                ['efgh']
            ),
            (  # search by company name partial
                {'original_query': 'Venus'},
                ['efgh']
            ),
            (  # search by subtotal_cost
                {'original_query': '2000'},
                ['efgh']
            ),
            (  # search by total_cost
                {'original_query': '2400'},
                ['efgh']
            ),
            (  # search by reference
                {'reference': 'efgh'},
                ['efgh']
            ),
            (  # search by reference partial
                {'reference': 'efg'},
                ['efgh']
            ),
            (  # search by subtotal_cost
                {'subtotal_cost': 2000},
                ['efgh']
            ),
            (  # search by total_cost
                {'total_cost': 2400},
                ['efgh']
            ),
            (  # search by contact name exact
                {'contact_name': 'Jenny Cakeman'},
                ['efgh']
            ),
            (  # search by contact name partial
                {'contact_name': 'Jenny Cakem'},
                ['efgh']
            ),
            (  # search by company name exact
                {'company_name': 'Venus Ltd'},
                ['efgh']
            ),
            (  # search by company name partial
                {'company_name': 'Venus'},
                ['efgh']
            ),
            (  # search by trading name exact
                {'company_name': 'Earth outsourcing'},
                ['efgh']
            ),
            (  # search by trading name partial
                {'company_name': 'Earth'},
                ['efgh']
            ),
            (  # sort by created_on ASC
                {'sortby': 'created_on:asc'},
                ['abcd', 'efgh']
            ),
            (  # sort by created_on DESC
                {'sortby': 'created_on:desc'},
                ['efgh', 'abcd']
            ),
            (  # sort by modified_on ASC
                {'sortby': 'modified_on:asc'},
                ['abcd', 'efgh']
            ),
            (  # sort by modified_on DESC
                {'sortby': 'modified_on:desc'},
                ['efgh', 'abcd']
            ),
            (  # sort by delivery_date ASC
                {'sortby': 'delivery_date:asc'},
                ['abcd', 'efgh']
            ),
            (  # sort by delivery_date DESC
                {'sortby': 'delivery_date:desc'},
                ['efgh', 'abcd']
            ),
            (  # sort by payment_due_date ASC
                {'sortby': 'payment_due_date:asc'},
                ['abcd', 'efgh']
            ),
            (  # sort by payment_due_date DESC
                {'sortby': 'payment_due_date:desc'},
                ['efgh', 'abcd']
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

    def test_filter_by_company_id(self, setup_data):
        """Test that orders can be filtered by company id."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(
            url, {
                'company': Company.objects.get(name='Venus Ltd').pk
            },
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'efgh'

    def test_incorrect_dates_raise_validation_error(self, setup_data):
        """Test that if the dates are not in a valid format, the API return a validation error."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'created_on_before': 'invalid',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'created_on_before': ['Date is in incorrect format.']}

    def test_incorrect_primary_market_raise_validation_error(self, setup_data):
        """
        Test that if the primary_market is not in a valid format,
        then the API return a validation error.
        """
        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'primary_market': 'invalid',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'primary_market': ['"invalid" is not a valid UUID.']}

    def test_filter_by_assigned_to_assignee_adviser(self, setup_data):
        """Test that results can be filtered by assignee."""
        assignee = Order.objects.get(reference='efgh').assignees.first()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'assigned_to_adviser': assignee.adviser.pk
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'efgh'

    def test_filter_by_assigned_to_assignee_adviser_team(self, setup_data):
        """Test that results can be filtered by the assignee's team."""
        assignee = Order.objects.get(reference='efgh').assignees.first()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, {
            'assigned_to_team': assignee.adviser.dit_team.pk
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'efgh'


class TestGlobalSearch(APITestMixin):
    """Test global search for orders."""

    @pytest.mark.parametrize(
        'term,results',
        (
            (  # no filter => return all records
                '',
                ['abcd', 'efgh']
            ),
            (  # search by reference
                'efgh',
                ['efgh']
            ),
            (  # search by reference partial
                'efg',
                ['efgh']
            ),
            (  # search by contact name exact
                'Jenny Cakeman',
                ['efgh']
            ),
            (  # search by contact name partial
                'Jenny Cakem',
                ['efgh']
            ),
            (  # search by company name exact
                'Venus Ltd',
                ['efgh']
            ),
            (  # search by company name partial
                'Venus',
                ['efgh']
            ),
            (  # search by subtotal_cost
                '2000',
                ['efgh']
            ),
            (  # search by total_cost
                '2400',
                ['efgh']
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
