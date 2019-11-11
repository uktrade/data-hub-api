import datetime
from uuid import UUID, uuid4

import factory
import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import (
    AdviserFactory,
    CompanyFactory,
    ContactFactory,
)
from datahub.core import constants
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.search.sync_object import sync_object
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.user_event_log.constants import USER_EVENT_TYPES
from datahub.user_event_log.models import UserEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data():
    """Sets up the data and makes the ES client available."""
    ContactFactory(
        first_name='abc',
        last_name='defg',
        company__name='name0',
        company__trading_names=['trading0'],
    )
    ContactFactory(
        first_name='first',
        last_name='last',
        company__name='name1',
        company__trading_names=['trading1'],
    )
    InvestmentProjectFactory(
        name='abc defg',
        description='investmentproject1',
        estimated_land_date=datetime.datetime(2011, 6, 13, 9, 44, 31, 62870),
        project_manager=AdviserFactory(first_name='name 0', last_name='surname 0'),
        project_assurance_adviser=AdviserFactory(first_name='name 1', last_name='surname 1'),
        investor_company=CompanyFactory(name='name3', trading_names=['trading3']),
        client_relationship_manager=AdviserFactory(first_name='name 2', last_name='surname 2'),
        referral_source_adviser=AdviserFactory(first_name='name 3', last_name='surname 3'),
        client_contacts=[],
    )
    InvestmentProjectFactory(
        description='investmentproject2',
        estimated_land_date=datetime.datetime(2057, 6, 13, 9, 44, 31, 62870),
        project_manager=AdviserFactory(first_name='name 4', last_name='surname 4'),
        project_assurance_adviser=AdviserFactory(first_name='name 5', last_name='surname 5'),
        investor_company=CompanyFactory(name='name4', trading_names=['trading4']),
        client_relationship_manager=AdviserFactory(first_name='name 6', last_name='surname 6'),
        referral_source_adviser=AdviserFactory(first_name='name 7', last_name='surname 7'),
        client_contacts=[],
    )

    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    CompanyFactory(
        name='abc defg ltd',
        trading_names=['abc defg trading ltd'],
        address_1='1 Fake Lane',
        address_town='Downtown',
        address_country_id=country_uk,
    )
    CompanyFactory(
        name='abc defg us ltd',
        trading_names=['abc defg us trading ltd'],
        address_1='1 Fake Lane',
        address_town='Downtown',
        address_country_id=country_us,
        registered_address_country_id=country_us,
    )


class TestValidateViewAttributes:
    """Validates the field names specified in various class attributes on views."""

    def test_validate_filter_fields_are_in_serializer(self, search_view):
        """Validates that all filter fields exist in the serializer class."""
        valid_fields = search_view.serializer_class._declared_fields.keys()

        invalid_fields = frozenset(search_view.FILTER_FIELDS) - valid_fields
        assert not invalid_fields

    def test_validate_remap_fields_exist(self, search_view):
        """Validate that the values of REMAP_FIELDS are valid field paths."""
        mapping = search_view.search_app.es_model._doc_type.mapping

        invalid_fields = {
            field for field in search_view.REMAP_FIELDS.values()
            if not mapping.resolve_field(field)
        }

        assert not invalid_fields

    def test_validate_remap_fields_are_used_in_filters(self, search_view):
        """Validate that the values of REMAP_FIELDS are used in a filter."""
        assert not {
            field for field in search_view.REMAP_FIELDS if field not in search_view.FILTER_FIELDS
        }

    def test_validate_composite_filter_fields(self, search_view):
        """Validate that the values of COMPOSITE_FILTERS are valid field paths."""
        mapping = search_view.search_app.es_model._doc_type.mapping

        invalid_fields = {
            field
            for field_list in search_view.COMPOSITE_FILTERS.values()
            for field in field_list
            if not mapping.resolve_field(field)
            and field not in search_view.search_app.es_model.PREVIOUS_MAPPING_FIELDS
        }

        assert not invalid_fields


class TestValidateViewSortByAttributes:
    """Validates the various sort by attributes for each view (and the related serialiser)."""

    def test_sort_by_fields(self, search_view):
        """Validate that all sort by values are valid field paths."""
        serializer_class = search_view.serializer_class
        mapping = search_view.search_app.es_model._doc_type.mapping

        invalid_fields = {
            field
            for field in set(serializer_class.SORT_BY_FIELDS)
            if not mapping.resolve_field(search_view.es_sort_by_remappings.get(field, field))
        }

        assert not invalid_fields

    def test_sort_by_remapping_keys_are_sort_by_fields(self, search_view):
        """
        Validate that the keys of view.es_sort_by_remappings are in serializer.SORT_BY_FIELDS.
        """
        if not hasattr(search_view, 'es_sort_by_remappings'):
            return

        serializer_class = search_view.serializer_class

        invalid_fields = (
            search_view.es_sort_by_remappings.keys() - set(serializer_class.SORT_BY_FIELDS)
        )

        assert not invalid_fields


class TestValidateExportViewAttributes:
    """Validates the field names specified in class attributes on export views."""

    def test_validate_db_sort_by_remappings_keys(self, search_view):
        """Validate that the keys of db_sort_by_remappings are valid sort by fields."""
        if not hasattr(search_view, 'db_sort_by_remappings'):
            return

        serializer_class = search_view.serializer_class
        invalid_fields = (
            search_view.db_sort_by_remappings.keys() - set(serializer_class.SORT_BY_FIELDS)
        )
        assert not invalid_fields


class TestBasicSearch(APITestMixin):
    """
    Tests for SearchBasicAPIView.

    TODO: make these tests generic using `search_support` instead of relying on specific
    search apps.
    """

    def test_pagination(self, es_with_collector):
        """Tests the pagination."""
        total_records = 9
        page_size = 2

        ids = sorted((uuid4() for _ in range(total_records)))

        name = 'test record'

        CompanyFactory.create_batch(
            len(ids),
            id=factory.Iterator(ids),
            name=name,
            trading_names=[],
        )

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        for page in range((len(ids) + page_size - 1) // page_size):
            response = self.api_client.get(
                url,
                data={
                    'term': name,
                    'entity': 'company',
                    'offset': page * page_size,
                    'limit': page_size,
                },
            )

            assert response.status_code == status.HTTP_200_OK

            start = page * page_size
            end = start + page_size
            assert ids[start:end] == [UUID(company['id']) for company in response.data['results']]

    @pytest.mark.parametrize('entity', ('sloth', ))
    def test_400_with_invalid_entity(self, es_with_collector, entity):
        """Tests case where provided entity is invalid."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': 'test',
                'entity': entity,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'entity': [f'"{entity}" is not a valid choice.'],
        }

    def test_quality(self, es_with_collector, setup_data):
        """Tests quality of results."""
        CompanyFactory(name='The Risk Advisory Group', trading_names=[])
        CompanyFactory(name='The Advisory Group', trading_names=[])
        CompanyFactory(name='The Advisory', trading_names=[])
        CompanyFactory(name='The Advisories', trading_names=[])

        es_with_collector.flush_and_refresh()

        term = 'The Advisory'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        # results are in order of relevance
        assert [
            'The Advisory',
            'The Advisory Group',
            'The Risk Advisory Group',
        ] == [company['name'] for company in response.data['results']]

    def test_partial_match(self, es_with_collector, setup_data):
        """Tests partial matching."""
        CompanyFactory(name='Veryuniquename1', trading_names=[])
        CompanyFactory(name='Veryuniquename2', trading_names=[])
        CompanyFactory(name='Veryuniquename3', trading_names=[])
        CompanyFactory(name='Veryuniquename4', trading_names=[])

        es_with_collector.flush_and_refresh()

        term = 'Veryuniquenam'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

        # particular order is not important here, we just need all that partially match
        assert {
            'Veryuniquename1',
            'Veryuniquename2',
            'Veryuniquename3',
            'Veryuniquename4',
        } == {company['name'] for company in response.data['results']}

    def test_hyphen_match(self, es_with_collector, setup_data):
        """Tests hyphen query."""
        CompanyFactory(name='t-shirt', trading_names=[])
        CompanyFactory(name='tshirt', trading_names=[])
        CompanyFactory(name='electronic shirt', trading_names=[])
        CompanyFactory(name='t and e and a', trading_names=[])

        es_with_collector.flush_and_refresh()

        term = 't-shirt'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

        # order of relevance
        assert [
            't-shirt',
            'tshirt',
        ] == [company['name'] for company in response.data['results']]

    def test_search_by_id(self, es_with_collector, setup_data):
        """Tests exact id matching."""
        CompanyFactory(id='0fb3379c-341c-4dc4-b125-bf8d47b26baa')
        CompanyFactory(id='0fb2379c-341c-4dc4-b225-bf8d47b26baa')
        CompanyFactory(id='0fb4379c-341c-4dc4-b325-bf8d47b26baa')
        CompanyFactory(id='0fb5379c-341c-4dc4-b425-bf8d47b26baa')

        es_with_collector.flush_and_refresh()

        term = '0fb4379c-341c-4dc4-b325-bf8d47b26baa'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert '0fb4379c-341c-4dc4-b325-bf8d47b26baa' == response.data['results'][0]['id']

    def test_400_with_invalid_sortby(self, es):
        """Tests attempt to sort by non existent field."""
        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': 'Test',
                'entity': 'company',
                'sortby': 'some_field_that_doesnt_exist:asc',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_aggregations(self, es_with_collector, setup_data):
        """Tests basic aggregate query."""
        company = CompanyFactory(name='very_unique_company')
        ContactFactory(company=company)
        InvestmentProjectFactory(investor_company=company)

        es_with_collector.flush_and_refresh()

        term = 'very_unique_company'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'very_unique_company'

        aggregations = [
            {'count': 1, 'entity': 'company'},
            {'count': 1, 'entity': 'contact'},
            {'count': 1, 'entity': 'investment_project'},
        ]
        assert all(aggregation in response.data['aggregations'] for aggregation in aggregations)

    @pytest.mark.parametrize(
        'permission,permission_entity',
        (
            ('view_company', 'company'),
            ('view_contact', 'contact'),
            ('view_event', 'event'),
            ('view_all_interaction', 'interaction'),
            ('view_all_investmentproject', 'investment_project'),
            ('view_associated_investmentproject', 'investment_project'),
            ('view_order', 'order'),
        ),
    )
    @pytest.mark.parametrize(
        'entity',
        (
            'company',
            'contact',
            'event',
            'interaction',
            'investment_project',
            'order',
        ),
    )
    def test_permissions(self, es_with_collector, permission, permission_entity, entity):
        """Tests model permissions enforcement in basic search."""
        user = create_test_user(permission_codenames=[permission], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)

        InvestmentProjectFactory(created_by=user)
        CompanyFactory()
        ContactFactory()
        EventFactory()
        CompanyInteractionFactory()
        OrderFactory()

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(
            url,
            data={
                'term': '',
                'entity': entity,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert (response_data['count'] == 0) == (permission_entity != entity)

        assert len(response_data['aggregations']) == 1
        assert response_data['aggregations'][0]['entity'] == permission_entity

    def test_basic_search_no_permissions(self, es_with_collector):
        """Tests model permissions enforcement in basic search for a user with no permissions."""
        user = create_test_user(permission_codenames=[], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)

        InvestmentProjectFactory(created_by=user)
        CompanyFactory()
        ContactFactory()
        EventFactory()
        CompanyInteractionFactory()
        OrderFactory()

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(
            url,
            data={
                'term': '',
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0

        assert len(response_data['aggregations']) == 0


class TestFilteredSearch(APITestMixin):
    """
    Tests related to `SearchAPIView`.

    TODO: make these tests generic using `search_support` instead of relying on specific
    search apps.
    """

    def test_search_sort_asc_with_null_values(self, es_with_collector, setup_data):
        """Tests placement of null values in sorted results when order is ascending."""
        InvestmentProjectFactory(name='Earth 1', estimated_land_date=datetime.date(2010, 1, 1))
        InvestmentProjectFactory(name='Earth 2', estimated_land_date=None)

        es_with_collector.flush_and_refresh()

        term = 'Earth'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'estimated_land_date:asc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [
            ('Earth 2', None),
            ('Earth 1', '2010-01-01'),
        ] == [
            (investment['name'], investment['estimated_land_date'])
            for investment in response.data['results']
        ]

    def test_search_sort_desc_with_null_values(self, es_with_collector, setup_data):
        """Tests placement of null values in sorted results when order is descending."""
        InvestmentProjectFactory(name='Ether 1', estimated_land_date=datetime.date(2010, 1, 1))
        InvestmentProjectFactory(name='Ether 2', estimated_land_date=None)

        es_with_collector.flush_and_refresh()

        term = 'Ether'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'estimated_land_date:desc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [
            ('Ether 1', '2010-01-01'),
            ('Ether 2', None),
        ] == [
            (investment['name'], investment['estimated_land_date'])
            for investment in response.data['results']
        ]


class TestSearchExportAPIView(APITestMixin):
    """Tests for SearchExportAPIView."""

    def test_creates_user_event_log_entries(self, es_with_collector):
        """Tests that when an export is performed, a user event is recorded."""
        user = create_test_user(permission_codenames=['view_simplemodel'])
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:simplemodel-export')

        simple_obj = SimpleModel(name='test')
        simple_obj.save()
        sync_object(SimpleModelSearchApp, simple_obj.pk)

        es_with_collector.flush_and_refresh()

        frozen_time = datetime.datetime(2018, 1, 2, 12, 30, 50, tzinfo=utc)
        with freeze_time(frozen_time):
            response = api_client.post(
                url,
                data={
                    'name': 'test',
                },
            )

        assert response.status_code == status.HTTP_200_OK
        assert UserEvent.objects.count() == 1

        user_event = UserEvent.objects.first()
        assert user_event.adviser == user
        assert user_event.type == USER_EVENT_TYPES.search_export
        assert user_event.timestamp == frozen_time
        assert user_event.api_url_path == '/v3/search/simplemodel/export'
        assert user_event.data == {
            'args': {
                'limit': 100,
                'name': 'test',
                'offset': 0,
                'original_query': '',
                'sortby': None,
            },
            'num_results': 1,
        }
