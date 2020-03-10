import datetime

import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.search.sync_object import sync_object
from datahub.search.test.search_support.models import RelatedModel, SimpleModel
from datahub.search.test.search_support.simplemodel import SimpleModelSearchApp
from datahub.user_event_log.constants import UserEventType
from datahub.user_event_log.models import UserEvent

pytestmark = pytest.mark.django_db


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
        entities = search_view().get_entities()
        mappings = [entity._doc_type.mapping for entity in entities]

        invalid_fields = {
            field
            for field_list in search_view.COMPOSITE_FILTERS.values()
            for field in field_list
            if not any(mapping.resolve_field(field) for mapping in mappings)
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
    """Tests for SearchBasicAPIView."""

    def test_pagination(self, es_with_collector, search_support_user):
        """Tests the pagination."""
        total_records = 9
        page_size = 2

        name = 'test record'

        objects = [SimpleModel(name=name) for _ in range(total_records)]

        for obj in objects:
            obj.save()

        # Note: id is a Keyword field, so string sorting must be used
        ids = sorted((obj.id for obj in objects), key=str)

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        for page in range((total_records + page_size - 1) // page_size):
            response = api_client.get(
                url,
                data={
                    'term': name,
                    'entity': 'simplemodel',
                    'offset': page * page_size,
                    'limit': page_size,
                },
            )

            assert response.status_code == status.HTTP_200_OK

            start = page * page_size
            end = start + page_size
            assert ids[start:end] == [result['id'] for result in response.data['results']]

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

    def test_quality(self, es_with_collector, search_support_user):
        """Tests quality of results."""
        SimpleModel.objects.create(name='The Risk Advisory Group')
        SimpleModel.objects.create(name='The Advisory Group')
        SimpleModel.objects.create(name='The Advisory')
        SimpleModel.objects.create(name='The Advisories')

        es_with_collector.flush_and_refresh()

        term = 'The Advisory'

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': term,
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

        # results are in order of relevance
        assert [
            'The Advisory',
            'The Advisory Group',
            'The Risk Advisory Group',
        ] == [result['name'] for result in response.data['results']]

    def test_partial_match(self, es_with_collector, search_support_user):
        """Tests partial matching."""
        SimpleModel.objects.create(name='Veryuniquename1')
        SimpleModel.objects.create(name='Veryuniquename2')
        SimpleModel.objects.create(name='Veryuniquename3')
        SimpleModel.objects.create(name='Veryuniquename4')
        SimpleModel.objects.create(name='Nonmatchingobject')

        es_with_collector.flush_and_refresh()

        term = 'Veryuniquenam'

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': term,
                'entity': 'simplemodel',
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
        } == {result['name'] for result in response.data['results']}

    def test_hyphen_match(self, es_with_collector, search_support_user):
        """Tests hyphen query."""
        SimpleModel.objects.create(name='t-shirt')
        SimpleModel.objects.create(name='tshirt')
        SimpleModel.objects.create(name='electronic shirt')
        SimpleModel.objects.create(name='t and e and a')

        es_with_collector.flush_and_refresh()

        term = 't-shirt'

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': term,
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

        # order of relevance
        assert [
            't-shirt',
            'tshirt',
        ] == [result['name'] for result in response.data['results']]

    def test_search_by_id(self, es_with_collector, search_support_user):
        """Tests exact id matching."""
        SimpleModel.objects.create(id=1000)
        SimpleModel.objects.create(id=1002)
        SimpleModel.objects.create(id=1004)
        SimpleModel.objects.create(id=4560)

        es_with_collector.flush_and_refresh()

        term = '4560'

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': term,
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert 4560 == response.data['results'][0]['id']

    def test_400_with_invalid_sortby(self, es, search_support_user):
        """Tests attempt to sort by non existent field."""
        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': 'Test',
                'entity': 'simplemodel',
                'sortby': 'some_field_that_doesnt_exist:asc',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_aggregations(self, es_with_collector, search_support_user):
        """Tests basic aggregate query."""
        simple_obj = SimpleModel.objects.create(name='very_unique_name')
        RelatedModel.objects.create(simpleton=simple_obj)

        unrelated_obj = SimpleModel.objects.create(name='unmatched_object')
        RelatedModel.objects.create(simpleton=unrelated_obj)

        es_with_collector.flush_and_refresh()

        term = 'very_unique_name'

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': term,
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'very_unique_name'

        aggregations = [
            {'count': 1, 'entity': 'simplemodel'},
            {'count': 1, 'entity': 'relatedmodel'},
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
        """
        Tests model permissions enforcement in basic search.

        TODO: we should test permissions relevant to a specific search app in the tests for that
            search app, and remove this test.
        """
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

        SimpleModel.objects.create(name='test')

        es_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        response = api_client.get(
            url,
            data={
                'term': '',
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 0

        assert len(response_data['aggregations']) == 0


class TestEntitySearch(APITestMixin):
    """Tests for `SearchAPIView`."""

    def test_search_sort_asc_with_null_values(self, es_with_collector, search_support_user):
        """Tests placement of null values in sorted results when order is ascending."""
        SimpleModel.objects.create(name='Earth 1', date=datetime.date(2010, 1, 1))
        SimpleModel.objects.create(name='Earth 2', date=None)

        es_with_collector.flush_and_refresh()

        api_client = self.create_api_client(user=search_support_user)
        url = reverse('api-v3:search:simplemodel')

        response = api_client.post(
            url,
            data={
                'original_query': '',
                'sortby': 'date:asc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert [
            ('Earth 2', None),
            ('Earth 1', '2010-01-01'),
        ] == [
            (obj['name'], obj['date'])
            for obj in response_data['results']
        ]

    def test_search_sort_desc_with_null_values(self, es_with_collector, search_support_user):
        """Tests placement of null values in sorted results when order is descending."""
        SimpleModel.objects.create(name='Ether 1', date=datetime.date(2010, 1, 1))
        SimpleModel.objects.create(name='Ether 2', date=None)

        es_with_collector.flush_and_refresh()

        api_client = self.create_api_client(user=search_support_user)
        url = reverse('api-v3:search:simplemodel')

        response = api_client.post(
            url,
            data={
                'original_query': '',
                'sortby': 'date:desc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        assert [
            ('Ether 1', '2010-01-01'),
            ('Ether 2', None),
        ] == [
            (obj['name'], obj['date'])
            for obj in response_data['results']
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
        assert user_event.type == UserEventType.SEARCH_EXPORT
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
