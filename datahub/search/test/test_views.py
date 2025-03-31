import datetime
from uuid import UUID

import factory
import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
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
        mapping = search_view.search_app.search_model._doc_type.mapping

        invalid_fields = {
            field
            for field in search_view.REMAP_FIELDS.values()
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
            and field not in search_view.search_app.search_model.PREVIOUS_MAPPING_FIELDS
        }

        assert not invalid_fields


class TestValidateViewSortByAttributes:
    """Validates the various sort by attributes for each view (and the related serialiser)."""

    def test_sort_by_fields(self, search_view):
        """Validate that all sort by values are valid field paths."""
        serializer_class = search_view.serializer_class
        mapping = search_view.search_app.search_model._doc_type.mapping

        invalid_fields = {
            field
            for field in set(serializer_class.SORT_BY_FIELDS)
            if not mapping.resolve_field(search_view.es_sort_by_remappings.get(field, field))
        }

        assert not invalid_fields

    def test_sort_by_remapping_keys_are_sort_by_fields(self, search_view):
        """Validate that the keys of view.es_sort_by_remappings are in serializer.SORT_BY_FIELDS.
        """
        if not hasattr(search_view, 'es_sort_by_remappings'):
            return

        serializer_class = search_view.serializer_class

        invalid_fields = search_view.es_sort_by_remappings.keys() - set(
            serializer_class.SORT_BY_FIELDS,
        )

        assert not invalid_fields


class TestValidateExportViewAttributes:
    """Validates the field names specified in class attributes on export views."""

    def test_validate_db_sort_by_remappings_keys(self, search_view):
        """Validate that the keys of db_sort_by_remappings are valid sort by fields."""
        if not hasattr(search_view, 'db_sort_by_remappings'):
            return

        serializer_class = search_view.serializer_class
        invalid_fields = search_view.db_sort_by_remappings.keys() - set(
            serializer_class.SORT_BY_FIELDS,
        )
        assert not invalid_fields


class TestBasicSearch(APITestMixin):
    """Tests for SearchBasicAPIView."""

    def test_pagination(self, opensearch_with_collector, search_support_user):
        """Tests the pagination."""
        total_records = 9
        page_size = 2

        name = 'test record'

        objects = [SimpleModel(name=name) for _ in range(total_records)]

        for obj in objects:
            obj.save()

        # Note: id is a Keyword field, so string sorting must be used
        ids = sorted((obj.id for obj in objects), key=str)

        opensearch_with_collector.flush_and_refresh()

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

    @pytest.mark.parametrize('entity', ('sloth',))
    def test_400_with_invalid_entity(self, opensearch_with_collector, entity):
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

    def test_quality(self, opensearch_with_collector, search_support_user):
        """Tests quality of results."""
        SimpleModel.objects.create(name='The Risk Advisory Group')
        SimpleModel.objects.create(name='The Advisory Group')
        SimpleModel.objects.create(name='The Advisory')
        SimpleModel.objects.create(name='The Advisories')
        SimpleModel.objects.create(name='The Group')

        opensearch_with_collector.flush_and_refresh()

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

    @pytest.mark.parametrize(
        'name,search_term,should_match',
        (
            ('The Risk Advisory Group', 'The Advisory', True),
            ('The Advisory Group', 'The Advisory', True),
            ('The Advisory', 'The Advisory', True),
            ('The Advisory', 'The Advasory', True),
            ('The Advisory', 'The Adviosry', True),
            ('The Advisory', 'The Adviosrys', True),
            ('The Advisories', 'The Advisory', False),
            ('The Group', 'The Advisory', False),
            ('Smarterlight Ltd', 'Smarterlight Ltd', True),
            ('Smarterlight Ltd', 'Smarterlight', True),
            ('Smarterlight', 'Smatterlight', True),
            ('Smarterlight Ltd', 'Smaxtec', False),
            ('Smarterlight Ltd', 'Omarterlight', False),
            ('Smarterlight Ltd', 'Sparterlight', False),
            ('Smarterlight Ltd', 'Smarterlight Inc', False),
            ('Charterhouse', 'Hotel', False),
            ('Block C, The Courtyard, 55 Charterhouse Street', 'Hotel', False),
        ),
    )
    def test_fuzzy_quality_single_field(
        self,
        opensearch_with_collector,
        search_support_user,
        name,
        search_term,
        should_match,
    ):
        """Tests quality of results for fuzzy matching.

        This should not only hit on exact matches, but also close matches.
        """
        SimpleModel.objects.create(name=name)
        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': search_term,
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        if should_match:
            assert response.data['count'] == 1
            assert response.data['results'][0]['name'] == name
        else:
            assert response.data['count'] == 0

    @pytest.mark.parametrize(
        'name,address,search_term,should_match',
        (
            ('Charterhouse', 'Block C, The Courtyard, 55 Charterhouse Street', 'Hotel', False),
            ('Charterhouse', 'Overlook Hotel, Courtyard, 55 Charterhouse', 'Hotel', True),
            ('Charterhouse', 'Overlook Hotel, Courtyard, 55 Charterhouse', 'Hotal', True),
            ('Charterhouse', 'Overlook Hotel, Courtyard, 55 Charterhouse', 'Hartleyhouse', False),
            ('Charterhouse', 'Overlook Hotel, Courtyard, 55 London Road', 'Chatterhouse', True),
        ),
    )
    def test_fuzzy_quality_multi_field(
        self,
        opensearch_with_collector,
        search_support_user,
        name,
        address,
        search_term,
        should_match,
    ):
        """Tests quality of results for fuzzy matching multiple fields.

        This should not only hit on exact matches, but also close matches.
        """
        SimpleModel.objects.create(name=name, address=address)
        opensearch_with_collector.flush_and_refresh()

        url = reverse('api-v3:search:basic')
        api_client = self.create_api_client(user=search_support_user)

        response = api_client.get(
            url,
            data={
                'term': search_term,
                'entity': 'simplemodel',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        if should_match:
            assert response.data['count'] == 1
            assert response.data['results'][0]['name'] == name
            assert response.data['results'][0]['address'] == address
        else:
            assert response.data['count'] == 0

    def test_fuzzy_quality_cross_fields(
        self,
        opensearch_with_collector,
        search_support_user,
    ):
        """Tests quality of results for fuzzy matching across multiple fields.

        Unfortunately we require "combined_fields" matching (introduced in OpenSearch
        v 7.13) to do fuzzy matching across multiple fields, but we should still be
        able to search for exact terms that can be divided across multiple fields.
        """
        SimpleModel.objects.create(name='The Risk Advisory Group', country='Canada')
        SimpleModel.objects.create(name='The Advisory', country='Canada')
        SimpleModel.objects.create(name='The Advisory Group', country='Canada')
        SimpleModel.objects.create(name='The Group', country='Canada')

        SimpleModel.objects.create(name='The Risk Advisory Group', country='France')
        SimpleModel.objects.create(name='The Advisory', country='France')
        SimpleModel.objects.create(name='The Advisory Group', country='France')
        SimpleModel.objects.create(name='The Group', country='France')

        opensearch_with_collector.flush_and_refresh()

        term = 'The Advisory Canada'

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
            ('The Advisory', 'Canada'),
            ('The Advisory Group', 'Canada'),
            ('The Risk Advisory Group', 'Canada'),
        ] == [(result['name'], result['country']) for result in response.data['results']]

    def test_fuzzy_quality_cross_fields_address_below_name(
        self,
        opensearch_with_collector,
        search_support_user,
    ):
        """Tests that name is more important than other fields in cross field matches.
        """
        SimpleModel.objects.create(name='Smaxtec Limited', address='')
        SimpleModel.objects.create(name='Newsmax Media (HQ Florida)', address='')
        SimpleModel.objects.create(name='Smooth Notebooks', address='Smaxet House')
        SimpleModel.objects.create(name='Other Notebooks', address='Maxet House')

        opensearch_with_collector.flush_and_refresh()

        term = 'Smax'

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
            'Smaxtec Limited',
            'Newsmax Media (HQ Florida)',
            'Smooth Notebooks',
        ] == [result['name'] for result in response.data['results']]

    def test_partial_match(self, opensearch_with_collector, search_support_user):
        """Tests partial matching."""
        SimpleModel.objects.create(name='Veryuniquename1')
        SimpleModel.objects.create(name='Veryuniquename2')
        SimpleModel.objects.create(name='Veryuniquename3')
        SimpleModel.objects.create(name='Veryuniquename4')
        SimpleModel.objects.create(name='Nonmatchingobject')

        opensearch_with_collector.flush_and_refresh()

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

    def test_hyphen_match(self, opensearch_with_collector, search_support_user):
        """Tests hyphen query."""
        SimpleModel.objects.create(name='t-shirt')
        SimpleModel.objects.create(name='tshirt')
        SimpleModel.objects.create(name='electronic shirt')
        SimpleModel.objects.create(name='t and e and a')

        opensearch_with_collector.flush_and_refresh()

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

    def test_search_by_id(self, opensearch_with_collector, search_support_user):
        """Tests exact id matching."""
        SimpleModel.objects.create(id=1000)
        SimpleModel.objects.create(id=1002)
        SimpleModel.objects.create(id=1004)
        SimpleModel.objects.create(id=4560)

        opensearch_with_collector.flush_and_refresh()

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

    def test_400_with_invalid_sortby(self, opensearch, search_support_user):
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

    def test_aggregations(self, opensearch_with_collector, search_support_user):
        """Tests basic aggregate query."""
        simple_obj = SimpleModel.objects.create(name='very_unique_name')
        RelatedModel.objects.create(simpleton=simple_obj)

        unrelated_obj = SimpleModel.objects.create(name='unmatched_object')
        RelatedModel.objects.create(simpleton=unrelated_obj)

        opensearch_with_collector.flush_and_refresh()

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
            ('view_advisor', 'adviser'),
        ),
    )
    @pytest.mark.parametrize(
        'entity',
        ('company', 'contact', 'event', 'interaction', 'investment_project', 'order', 'adviser'),
    )
    def test_permissions(self, opensearch_with_collector, permission, permission_entity, entity):
        """Tests model permissions enforcement in basic search.

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
        AdviserFactory()

        opensearch_with_collector.flush_and_refresh()

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

    def test_basic_search_no_permissions(self, opensearch_with_collector):
        """Tests model permissions enforcement in basic search for a user with no permissions."""
        user = create_test_user(permission_codenames=[], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)

        SimpleModel.objects.create(name='test')

        opensearch_with_collector.flush_and_refresh()

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

    def test_search_sort_asc_with_null_values(
        self,
        opensearch_with_collector,
        search_support_user,
    ):
        """Tests placement of null values in sorted results when order is ascending."""
        SimpleModel.objects.create(name='Earth 1', date=datetime.date(2010, 1, 1))
        SimpleModel.objects.create(name='Earth 2', date=None)

        opensearch_with_collector.flush_and_refresh()

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
        ] == [(obj['name'], obj['date']) for obj in response_data['results']]

    def test_search_sort_desc_with_null_values(
        self,
        opensearch_with_collector,
        search_support_user,
    ):
        """Tests placement of null values in sorted results when order is descending."""
        SimpleModel.objects.create(name='Ether 1', date=datetime.date(2010, 1, 1))
        SimpleModel.objects.create(name='Ether 2', date=None)

        opensearch_with_collector.flush_and_refresh()

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
        ] == [(obj['name'], obj['date']) for obj in response_data['results']]

    def test_sector_descends_filter_excludes_ancestors_for_interactions(
        self,
        hierarchical_sectors,
        opensearch_with_collector,
    ):
        """Test that the sector_descends filter excludes ancestor sectors
        (where a child sector already exists) for interactions.

        """
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        # Create companies in each sector
        companies = CompanyFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )

        # Create interactions for each company
        company_interactions = CompanyInteractionFactory.create_batch(
            num_sectors,
            company=factory.Iterator(companies),
        )

        # Make sure all sectors and interactions are in OpenSearch
        opensearch_with_collector.flush_and_refresh()

        # Retrieve youngest descendant sector
        youngest_descendant_sector_id = hierarchical_sectors[-1].pk
        # Pre-fetch all ancestors
        ancestors = hierarchical_sectors[-1].get_ancestors()
        ancestor_uuids = set(ancestors.values_list('id', flat=True))

        # Test API endpoint with youngest descendant sector
        url = reverse('api-v3:search:interaction')
        body = {
            'sector_descends': sectors_ids,
        }
        response = self.api_client.post(url, body)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        # Expecting interactions associated with the youngest descendant sector
        expected_ids = {
            interaction.pk
            for interaction in company_interactions
            if interaction.company.sector_id == youngest_descendant_sector_id
        }

        actual_ids = {
            UUID(interaction['id']) for interaction in response_data['results']
        }

        # Assert that no ancestor sectors' interactions are in the results
        assert response_data['count'] == 1
        assert actual_ids == expected_ids
        assert all(ancestor_id not in actual_ids for ancestor_id in ancestor_uuids)

    def test_sector_descends_filter_excludes_ancestors_for_companies(
        self,
        hierarchical_sectors,
        opensearch_with_collector,
    ):
        """Test that the sector_descends filter excludes ancestor sectors
        (where a child sector already exists) for companies.

        """
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        # Create companies in each sector
        companies = CompanyFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids),
        )

        # Make sure all sectors and interactions are in OpenSearch
        opensearch_with_collector.flush_and_refresh()

        # Retrieve youngest descendant sector
        youngest_descendant_sector_id = hierarchical_sectors[-1].pk
        # Pre-fetch all ancestors
        ancestors = hierarchical_sectors[-1].get_ancestors()
        ancestor_uuids = set(ancestors.values_list('id', flat=True))

        # Test API endpoint with youngest descendant sector
        url = reverse('api-v4:search:company')
        body = {
            'sector_descends': sectors_ids,
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        # Expecting companies associated with the youngest descendant sector
        expected_ids = {
            company.pk
            for company in companies
            if company.sector_id == youngest_descendant_sector_id
        }

        actual_ids = {UUID(company['id']) for company in response_data['results']}

        # Assert that no ancestor sectors' companies are in the results
        assert response_data['count'] == 1
        assert actual_ids == expected_ids
        assert all(ancestor_id not in actual_ids for ancestor_id in ancestor_uuids)


class TestSearchExportAPIView(APITestMixin):
    """Tests for SearchExportAPIView."""

    def test_creates_user_event_log_entries(self, opensearch_with_collector):
        """Tests that when an export is performed, a user event is recorded."""
        user = create_test_user(permission_codenames=['view_simplemodel'])
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:simplemodel-export')

        simple_obj = SimpleModel(name='test')
        simple_obj.save()
        sync_object(SimpleModelSearchApp, simple_obj.pk)

        opensearch_with_collector.flush_and_refresh()

        frozen_time = datetime.datetime(2018, 1, 2, 12, 30, 50, tzinfo=datetime.timezone.utc)
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
