from cgi import parse_header
from csv import DictReader
from decimal import Decimal
from io import StringIO
from uuid import UUID

import factory
import pytest
from dateutil.parser import parse as dateutil_parse
from django.conf import settings
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.models import Company
from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_csv_data,
    get_attr_or_none,
    random_obj_for_queryset,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.order.constants import OrderStatus
from datahub.omis.order.models import Order, OrderPermission
from datahub.omis.order.test.factories import (
    OrderAssigneeFactory,
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderSubscriberFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithCancelledQuoteFactory,
    OrderWithOpenQuoteFactory,
    OrderWithoutAssigneesFactory,
    OrderWithoutLeadAssigneeFactory,
)
from datahub.omis.payment.constants import RefundStatus
from datahub.omis.payment.test.factories import (
    ApprovedRefundFactory,
    RequestedRefundFactory,
)
from datahub.search.omis.views import SearchOrderExportAPIView

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data(es_with_collector):
    """Sets up data for the tests."""
    with freeze_time('2017-01-01 13:00:00'):
        company = CompanyFactory(
            name='Mercury trading',
            trading_names=[],
        )
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
            completed_on=dateutil_parse('2018-05-01T13:00:00Z'),
            vat_verified=False,
        )
        OrderSubscriberFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.healthcare_uk.value.id),
        )
        OrderAssigneeFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.tees_valley_lep.value.id),
            estimated_time=60,
        )

    with freeze_time('2017-02-01 13:00:00'):
        company = CompanyFactory(
            name='Venus Ltd',
            trading_names=['Maine Coon', 'Egyptian Mau', '3a'],
        )
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
            completed_on=dateutil_parse('2018-06-01T13:00:00Z'),
            vat_verified=False,
        )
        OrderSubscriberFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.td_events_healthcare.value.id),
        )
        OrderAssigneeFactory(
            order=order,
            adviser=AdviserFactory(dit_team_id=constants.Team.food_from_britain.value.id),
            estimated_time=120,
        )

    es_with_collector.flush_and_refresh()


@pytest.fixture
def setup_subtotal_cost_data(es_with_collector):
    """
    Setup Order data for total subtotal cost test.

    Order will have a reference that is a string representation of the resulting subtotal_cost.
    Subtotal cost must be three-digit because the test is choosing orders by their
    reference. The reference filter is built with a trigram so this way we can
    avoid ambiguity.
    """
    subtotal_costs = (100, 200, 300, 400, 500)

    for subtotal_cost in subtotal_costs:
        order = OrderFactory(
            reference=str(subtotal_cost),
            discount_value=0,
            assignees=[],
        )
        OrderAssigneeFactory(
            order=order,
            estimated_time=subtotal_cost * 60 // order.hourly_rate.rate_value,
        )

    es_with_collector.flush_and_refresh()


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
                ['efgh', 'abcd'],
            ),
            (  # pagination
                {'limit': 1, 'offset': 1},
                ['abcd'],
            ),
            (  # filter by primary market
                {'primary_market': constants.Country.france.value.id},
                ['efgh'],
            ),
            (  # filter by uk region
                {'uk_region': constants.UKRegion.east_midlands.value.id},
                ['efgh'],
            ),
            (  # filter by completed_on_before and completed_on_after
               # note that both dates are inclusive
                {
                    'completed_on_before': '2018-06-01',
                    'completed_on_after': '2018-05-01',
                    'sortby': 'created_on:asc',
                },
                ['abcd', 'efgh'],
            ),
            (  # filter by completed_on_before only
                {'completed_on_before': '2018-05-01'},
                ['abcd'],
            ),
            (  # filter by completed_on_before only
                {'completed_on_before': '2018-04-30'},
                [],
            ),
            (  # filter by completed_on_after only
                {'completed_on_after': '2018-06-01'},
                ['efgh'],
            ),
            (  # filter by completed_on_after only
                {'completed_on_after': '2018-06-02'},
                [],
            ),
            (  # filter by a range of date for created_on
                {
                    'created_on_before': '2017-02-02',
                    'created_on_after': '2017-02-01',
                },
                ['efgh'],
            ),
            (  # filter by created_on_before only
                {'created_on_before': '2017-01-15'},
                ['abcd'],
            ),
            (  # filter by created_on_after only
                {'created_on_after': '2017-01-15'},
                ['efgh'],
            ),
            (  # filter by delivery_date_before and delivery_date_after
                {
                    'delivery_date_before': '2018-02-02',
                    'delivery_date_after': '2018-02-01',
                },
                ['efgh'],
            ),
            (  # filter by delivery_date_before only
                {'delivery_date_before': '2018-01-15'},
                ['abcd'],
            ),
            (  # filter by delivery_date_after only
                {'delivery_date_after': '2018-01-15'},
                ['efgh'],
            ),
            (  # filter by status
                {'status': 'quote_awaiting_acceptance'},
                ['efgh'],
            ),
            (  # invalid status => no results
                {'status': 'invalid'},
                [],
            ),
            (  # search by reference
                {'original_query': 'efgh'},
                ['efgh'],
            ),
            (  # search by reference partial
                {'original_query': 'efg'},
                ['efgh'],
            ),
            (  # search by contact name exact
                {'original_query': 'Jenny Cakeman'},
                ['efgh'],
            ),
            (  # search by contact name partial
                {'original_query': 'Jenny Cakem'},
                ['efgh'],
            ),
            (  # search by company name exact
                {'original_query': 'Venus Ltd'},
                ['efgh'],
            ),
            (  # search by company name partial
                {'original_query': 'Venus'},
                ['efgh'],
            ),
            (  # search by subtotal_cost
                {'original_query': '2000'},
                ['efgh'],
            ),
            (  # search by total_cost
                {'original_query': '2400'},
                ['efgh'],
            ),
            (  # search by reference
                {'reference': 'efgh'},
                ['efgh'],
            ),
            (  # search by reference partial
                {'reference': 'efg'},
                ['efgh'],
            ),
            (  # search by subtotal_cost
                {'subtotal_cost': 2000},
                ['efgh'],
            ),
            (  # search by total_cost
                {'total_cost': 2400},
                ['efgh'],
            ),
            (  # search by contact name exact
                {'contact_name': 'Jenny Cakeman'},
                ['efgh'],
            ),
            (  # search by contact name partial
                {'contact_name': 'Jenny Cakem'},
                ['efgh'],
            ),
            (  # search by company name exact
                {'company_name': 'Venus Ltd'},
                ['efgh'],
            ),
            (  # search by company name partial
                {'company_name': 'Venus'},
                ['efgh'],
            ),
            (  # search by trading names exact
                {'company_name': 'Maine Coon Egyptian Mau'},
                ['efgh'],
            ),
            (  # search by trading names partial
                {'company_name': 'ine pti'},
                ['efgh'],
            ),
            (  # search by short trading names
                {'company_name': '3a'},
                ['efgh'],
            ),
            (  # sort by created_on ASC
                {'sortby': 'created_on:asc'},
                ['abcd', 'efgh'],
            ),
            (  # sort by created_on DESC
                {'sortby': 'created_on:desc'},
                ['efgh', 'abcd'],
            ),
            (  # sort by modified_on ASC
                {'sortby': 'modified_on:asc'},
                ['abcd', 'efgh'],
            ),
            (  # sort by modified_on DESC
                {'sortby': 'modified_on:desc'},
                ['efgh', 'abcd'],
            ),
            (  # sort by delivery_date ASC
                {'sortby': 'delivery_date:asc'},
                ['abcd', 'efgh'],
            ),
            (  # sort by delivery_date DESC
                {'sortby': 'delivery_date:desc'},
                ['efgh', 'abcd'],
            ),
            (  # sort by payment_due_date ASC
                {'sortby': 'payment_due_date:asc'},
                ['abcd', 'efgh'],
            ),
            (  # sort by payment_due_date DESC
                {'sortby': 'payment_due_date:desc'},
                ['efgh', 'abcd'],
            ),
        ),
    )
    def test_search(self, setup_data, data, results):
        """Test search results."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == len(results)
        assert [
            item['reference'] for item in response.json()['results']
        ] == results

    @pytest.mark.parametrize(
        'post_data,expected_total_subtotal_cost',
        (
            (  # no filter => return all records
                {},
                1500,
            ),
            (
                {'reference': ['100', '200']},
                300,
            ),
            (  # order with '150' reference doesn't exist
                {'reference': ['500', '150']},
                500,
            ),
            (
                {'reference': ['100', '200', '500']},
                800,
            ),
            (  # order with '50' reference doesn't exist
                {'reference': ['100', '50', '300', '400']},
                800,
            ),
            (  # order with such reference doesn't exist
                {'reference': '900'},
                0,
            ),
        ),
    )
    def test_search_orders_total_net_cost_value(
        self,
        setup_subtotal_cost_data,
        post_data,
        expected_total_subtotal_cost,
    ):
        """Test that search orders result contains correct total subtotal_cost."""
        url = reverse('api-v3:search:order')
        response = self.api_client.post(url, post_data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        subtotal_cost_total = response_data['summary']['total_subtotal_cost']
        assert subtotal_cost_total == expected_total_subtotal_cost

    def test_filter_by_company_id(self, setup_data):
        """Test that orders can be filtered by company id."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(
            url,
            data={
                'company': Company.objects.get(name='Venus Ltd').pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'efgh'

    def test_incorrect_dates_raise_validation_error(self, setup_data):
        """Test that if the dates are not in a valid format, the API return a validation error."""
        url = reverse('api-v3:search:order')

        response = self.api_client.post(
            url,
            data={
                'created_on_before': 'invalid',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'created_on_before': ['Date is in incorrect format.']}

    def test_incorrect_primary_market_raise_validation_error(self, setup_data):
        """
        Test that if the primary_market is not in a valid format,
        then the API return a validation error.
        """
        url = reverse('api-v3:search:order')

        response = self.api_client.post(
            url,
            data={
                'primary_market': 'invalid',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {'primary_market': ['Must be a valid UUID.']}

    @pytest.mark.parametrize(
        'sector_level',
        (0, 1, 2),
    )
    def test_sector_descends_filter(self, hierarchical_sectors, es_with_collector, sector_level):
        """Test the sector_descends filter."""
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        orders = OrderFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )
        OrderFactory.create_batch(
            3,
            sector=factory.LazyFunction(lambda: random_obj_for_queryset(
                Sector.objects.exclude(pk__in=sectors_ids),
            )),
        )

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:order')
        body = {
            'sector_descends': hierarchical_sectors[sector_level].pk,
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == num_sectors - sector_level

        actual_ids = {UUID(order['id']) for order in response_data['results']}
        expected_ids = {order.pk for order in orders[sector_level:]}
        assert actual_ids == expected_ids

    def test_filter_by_assigned_to_assignee_adviser(self, setup_data):
        """Test that results can be filtered by assignee."""
        assignee = Order.objects.get(reference='efgh').assignees.first()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(
            url,
            data={
                'assigned_to_adviser': assignee.adviser.pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'efgh'

    def test_filter_by_assigned_to_assignee_adviser_team(self, setup_data):
        """Test that results can be filtered by the assignee's team."""
        assignee = Order.objects.get(reference='efgh').assignees.first()

        url = reverse('api-v3:search:order')

        response = self.api_client.post(
            url,
            data={
                'assigned_to_team': assignee.adviser.dit_team.pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == 1
        assert response.json()['results'][0]['reference'] == 'efgh'


class TestOrderExportView(APITestMixin):
    """Tests the OMIS order export view."""

    @pytest.mark.parametrize(
        'permissions', (
            (),
            (f'order.{OrderPermission.view}',),
            (f'order.{OrderPermission.export}',),
        ),
    )
    def test_user_without_permission_cannot_export(self, es, permissions):
        """Test that a user without the correct permissions cannot export data."""
        user = create_test_user(dit_team=TeamFactory(), permission_codenames=permissions)
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:order-export')
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'request_sortby,orm_ordering',
        (
            ('created_on', 'created_on'),
            ('created_on:desc', '-created_on'),
            ('modified_on', 'modified_on'),
            ('modified_on:desc', '-modified_on'),
            ('delivery_date', 'delivery_date'),
            ('delivery_date:desc', '-delivery_date'),
        ),
    )
    def test_export(
        self,
        es_with_collector,
        request_sortby,
        orm_ordering,
    ):
        """Test export of interaction search results."""
        factories = (
            OrderCancelledFactory,
            OrderCompleteFactory,
            OrderFactory,
            OrderPaidFactory,
            OrderSubscriberFactory,
            OrderWithAcceptedQuoteFactory,
            OrderWithCancelledQuoteFactory,
            OrderWithOpenQuoteFactory,
            OrderWithoutAssigneesFactory,
            OrderWithoutLeadAssigneeFactory,
            ApprovedRefundFactory,
            ApprovedRefundFactory,
            RequestedRefundFactory,
        )

        order_with_multiple_refunds = OrderPaidFactory()
        ApprovedRefundFactory(
            order=order_with_multiple_refunds,
            requested_amount=order_with_multiple_refunds.total_cost / 5,
        )
        ApprovedRefundFactory(
            order=order_with_multiple_refunds,
            requested_amount=order_with_multiple_refunds.total_cost / 4,
        )
        ApprovedRefundFactory(
            order=order_with_multiple_refunds,
            requested_amount=order_with_multiple_refunds.total_cost / 3,
        )

        for factory_ in factories:
            factory_.create_batch(2)

        es_with_collector.flush_and_refresh()

        data = {}
        if request_sortby:
            data['sortby'] = request_sortby

        url = reverse('api-v3:search:order-export')

        with freeze_time('2018-01-01 11:12:13'):
            response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Type')) == ('text/csv', {'charset': 'utf-8'})
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {'filename': 'Data Hub - Orders - 2018-01-01-11-12-13.csv'},
        )

        sorted_orders = Order.objects.order_by(orm_ordering, 'pk')
        reader = DictReader(StringIO(response.getvalue().decode('utf-8-sig')))

        assert reader.fieldnames == list(SearchOrderExportAPIView.field_titles.values())
        sorted_orders_and_refunds = (
            (order, order.refunds.filter(status=RefundStatus.approved))
            for order in sorted_orders
        )

        expected_row_data = [
            {
                'Order reference': order.reference,
                'Net price': Decimal(order.subtotal_cost) / 100,
                'Net refund': Decimal(
                    sum(refund.net_amount for refund in refunds),
                ) / 100 if refunds else None,
                'Status': order.get_status_display(),
                'Link': order.get_datahub_frontend_url(),
                'Sector': order.sector.name,
                'Market': order.primary_market.name,
                'UK region': order.uk_region.name,
                'Company': order.company.name,
                'Company country':
                    order.company.address_country.name,
                'Company UK region': get_attr_or_none(order, 'company.uk_region.name'),
                'Company link':
                    f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["company"]}'
                    f'/{order.company.pk}',
                'Contact': order.contact.name,
                'Contact job title': order.contact.job_title,
                'Contact link':
                    f'{settings.DATAHUB_FRONTEND_URL_PREFIXES["contact"]}'
                    f'/{order.contact.pk}',
                'Lead adviser': get_attr_or_none(order.get_lead_assignee(), 'adviser.name'),
                'Created by team': get_attr_or_none(order, 'created_by.dit_team.name'),
                'Date created': order.created_on,
                'Delivery date': order.delivery_date,
                'Date quote sent': get_attr_or_none(order, 'quote.created_on'),
                'Date quote accepted': get_attr_or_none(order, 'quote.accepted_on'),
                'Date payment received': order.paid_on,
                'Date completed': order.completed_on,
            }
            for order, refunds in sorted_orders_and_refunds
        ]

        assert list(dict(row) for row in reader) == format_csv_data(expected_row_data)


class TestGlobalSearch(APITestMixin):
    """Test global search for orders."""

    @pytest.mark.parametrize(
        'term,expected_results',
        (
            (  # no filter => return all records
                '',
                ['abcd', 'efgh'],
            ),
            (  # search by reference
                'efgh',
                ['efgh'],
            ),
            (  # search by reference partial
                'efg',
                ['efgh'],
            ),
            (  # search by contact name exact
                'Jenny Cakeman',
                ['efgh'],
            ),
            (  # search by contact name partial
                'Jenny Cakem',
                ['efgh'],
            ),
            (  # search by company name exact
                'Venus Ltd',
                ['efgh'],
            ),
            (  # search by company name partial
                'Venus',
                ['efgh'],
            ),
            (  # search by subtotal_cost
                '2000',
                ['efgh'],
            ),
            (  # search by total_cost
                '2400',
                ['efgh'],
            ),
        ),
    )
    def test_search(self, setup_data, term, expected_results):
        """Test search results."""
        url = reverse('api-v3:search:basic')

        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'order',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()['results']) == len(expected_results)
        actual_results = sorted(
            item['reference']
            for item in response.json()['results']
        )
        assert actual_results == expected_results
