import datetime
from uuid import UUID, uuid4

import factory
import pytest
from django.utils.timezone import utc
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.event.test.factories import EventFactory
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from datahub.omis.order.test.factories import OrderFactory
from datahub.search.sync_async import sync_object_async
from datahub.search.test.search_support.models import SimpleModel
from datahub.search.test.search_support.simplemodel.models import ESSimpleModel
from datahub.search.test.utils import model_has_field_path
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
        company__alias='trading0',
    )
    ContactFactory(
        first_name='first',
        last_name='last',
        company__name='name1',
        company__alias='trading1',
    )
    InvestmentProjectFactory(
        name='abc defg',
        description='investmentproject1',
        estimated_land_date=datetime.datetime(2011, 6, 13, 9, 44, 31, 62870),
        project_manager=AdviserFactory(first_name='name 0', last_name='surname 0'),
        project_assurance_adviser=AdviserFactory(first_name='name 1', last_name='surname 1'),
        investor_company=CompanyFactory(name='name3', alias='trading3'),
        client_relationship_manager=AdviserFactory(first_name='name 2', last_name='surname 2'),
        referral_source_adviser=AdviserFactory(first_name='name 3', last_name='surname 3'),
        client_contacts=[],
    )
    InvestmentProjectFactory(
        description='investmentproject2',
        estimated_land_date=datetime.datetime(2057, 6, 13, 9, 44, 31, 62870),
        project_manager=AdviserFactory(first_name='name 4', last_name='surname 4'),
        project_assurance_adviser=AdviserFactory(first_name='name 5', last_name='surname 5'),
        investor_company=CompanyFactory(name='name4', alias='trading4'),
        client_relationship_manager=AdviserFactory(first_name='name 6', last_name='surname 6'),
        referral_source_adviser=AdviserFactory(first_name='name 7', last_name='surname 7'),
        client_contacts=[],
    )

    country_uk = constants.Country.united_kingdom.value.id
    country_us = constants.Country.united_states.value.id
    CompanyFactory(
        name='abc defg ltd',
        alias='abc defg trading ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_uk,
    )
    CompanyFactory(
        name='abc defg us ltd',
        alias='abc defg us trading ltd',
        trading_address_1='1 Fake Lane',
        trading_address_town='Downtown',
        trading_address_country_id=country_us,
        registered_address_country_id=country_us,
    )


class TestValidateViewAttributes:
    """Validates the field names specified in various class attributes on views."""

    def test_validate_filter_fields_are_in_serializer(self, search_app):
        """Validates that all filter fields exist in the serializer class."""
        view = search_app.view
        valid_fields = view.serializer_class._declared_fields.keys()

        invalid_fields = frozenset(view.FILTER_FIELDS) - valid_fields
        assert not invalid_fields

    def test_validate_remap_fields_exist(self, search_app):
        """Validate that the values of REMAP_FIELDS are valid field paths."""
        view = search_app.view

        invalid_fields = {
            field for field in view.REMAP_FIELDS.values()
            if not model_has_field_path(search_app.es_model, field)
        }

        assert not invalid_fields

    def test_validate_remap_fields_are_used_in_filters(self, search_app):
        """Validate that the values of REMAP_FIELDS are used in a filter."""
        view = search_app.view

        assert not {field for field in view.REMAP_FIELDS if field not in view.FILTER_FIELDS}

    def test_validate_composite_filter_fields(self, search_app):
        """Validate that the values of COMPOSITE_FILTERS are valid field paths."""
        view = search_app.view

        invalid_fields = {
            field
            for field_list in view.COMPOSITE_FILTERS.values()
            for field in field_list
            if not model_has_field_path(search_app.es_model, field)
            and field not in search_app.es_model.PREVIOUS_MAPPING_FIELDS
        }

        assert not invalid_fields


class TestValidateExportViewAttributes:
    """Validates the field names specified in class attributes on export views."""

    def test_validate_sort_by_remappings(self, search_app):
        """Validate that the values of sort_by_remappings are valid field paths."""
        view = search_app.export_view

        if not view:
            return

        invalid_fields = {
            field
            for field in view.sort_by_remappings
            if not model_has_field_path(search_app.es_model, field)
            and field not in search_app.es_model.PREVIOUS_MAPPING_FIELDS
        }

        assert not invalid_fields


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_basic_search_paging(self, setup_es, setup_data):
        """Tests pagination of results."""
        setup_es.indices.refresh()

        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'entity': 'company',
                'offset': 1,
                'limit': 1,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'sortby',
        (
            {},
            {'sortby': 'name:asc'},
            {'sortby': 'created_on:asc'},
        ),
    )
    def test_basic_search_consistent_paging(self, setup_es, sortby):
        """Tests if content placement is consistent between pages."""
        ids = sorted((uuid4() for _ in range(9)))

        name = 'test record'

        CompanyFactory.create_batch(
            len(ids),
            id=factory.Iterator(ids),
            name=name,
            alias='',
        )

        setup_es.indices.refresh()

        page_size = 2

        for page in range((len(ids) + page_size - 1) // page_size):
            url = reverse('api-v3:search:basic')
            response = self.api_client.get(
                url,
                data={
                    'term': name,
                    'entity': 'company',
                    'offset': page * page_size,
                    'limit': page_size,
                    **sortby,
                },
            )

            assert response.status_code == status.HTTP_200_OK

            start = page * page_size
            end = start + page_size
            assert ids[start:end] == [UUID(company['id']) for company in response.data['results']]

    def test_invalid_entity(self, setup_es, setup_data):
        """Tests case where provided entity is invalid."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': 'test',
                'entity': 'sloths',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_results_quality(self, setup_es, setup_data):
        """Tests quality of results."""
        CompanyFactory(name='The Risk Advisory Group')
        CompanyFactory(name='The Advisory Group')
        CompanyFactory(name='The Advisory')
        CompanyFactory(name='The Advisories')

        setup_es.indices.refresh()

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

        # results are in order of relevance if sortby is not applied
        assert [
            'The Advisory',
            'The Advisory Group',
            'The Risk Advisory Group',
        ] == [company['name'] for company in response.data['results']]

    def test_search_partial_match(self, setup_es, setup_data):
        """Tests partial matching."""
        CompanyFactory(name='Veryuniquename1')
        CompanyFactory(name='Veryuniquename2')
        CompanyFactory(name='Veryuniquename3')
        CompanyFactory(name='Veryuniquename4')

        setup_es.indices.refresh()

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

    def test_search_hyphen_match(self, setup_es, setup_data):
        """Tests hyphen query."""
        CompanyFactory(name='t-shirt')
        CompanyFactory(name='tshirt')
        CompanyFactory(name='electronic shirt')
        CompanyFactory(name='t and e and a')

        setup_es.indices.refresh()

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

    def test_search_id_match(self, setup_es, setup_data):
        """Tests exact id matching."""
        CompanyFactory(id='0fb3379c-341c-4dc4-b125-bf8d47b26baa')
        CompanyFactory(id='0fb2379c-341c-4dc4-b225-bf8d47b26baa')
        CompanyFactory(id='0fb4379c-341c-4dc4-b325-bf8d47b26baa')
        CompanyFactory(id='0fb5379c-341c-4dc4-b425-bf8d47b26baa')

        setup_es.indices.refresh()

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

    def test_search_sort_desc(self, setup_es, setup_data):
        """Tests sorting in descending order."""
        CompanyFactory(name='Water 1')
        CompanyFactory(name='water 2')
        CompanyFactory(name='water 3')
        CompanyFactory(name='Water 4')

        setup_es.indices.refresh()

        term = 'Water'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(
            url,
            data={
                'term': term,
                'sortby': 'name:desc',
                'entity': 'company',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert [
            'Water 4',
            'water 3',
            'water 2',
            'Water 1',
        ] == [company['name'] for company in response.data['results']]

    def test_search_sort_asc(self, setup_es, setup_data):
        """Tests sorting in ascending order."""
        CompanyFactory(name='Fire 4')
        CompanyFactory(name='fire 3')
        CompanyFactory(name='fire 2')
        CompanyFactory(name='Fire 1')

        setup_es.indices.refresh()

        term = 'Fire'

        url = reverse('api-v3:search:company')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'name:asc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert [
            'Fire 1',
            'fire 2',
            'fire 3',
            'Fire 4',
        ] == [company['name'] for company in response.data['results']]

    def test_search_sort_nested_desc(self, setup_es, setup_data):
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

        setup_es.indices.refresh()

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

    def test_search_sort_invalid(self, setup_es, setup_data):
        """Tests attempt to sort by non existent field."""
        CompanyFactory(name='Fire 4')
        CompanyFactory(name='fire 3')
        CompanyFactory(name='fire 2')
        CompanyFactory(name='Fire 1')

        setup_es.indices.refresh()

        term = 'Fire'

        url = reverse('api-v3:search:company')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'some_field_that_doesnt_exist:asc',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_search_sort_asc_with_null_values(self, setup_es, setup_data):
        """Tests placement of null values in sorted results when order is ascending."""
        InvestmentProjectFactory(name='Earth 1', total_investment=1000)
        InvestmentProjectFactory(name='Earth 2')

        setup_es.indices.refresh()

        term = 'Earth'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'total_investment:asc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [
            ('Earth 2', None),
            ('Earth 1', 1000),
        ] == [
            (investment['name'], investment['total_investment'])
            for investment in response.data['results']
        ]

    def test_search_sort_desc_with_null_values(self, setup_es, setup_data):
        """Tests placement of null values in sorted results when order is descending."""
        InvestmentProjectFactory(name='Ether 1', total_investment=1000)
        InvestmentProjectFactory(name='Ether 2')

        setup_es.indices.refresh()

        term = 'Ether'

        url = reverse('api-v3:search:investment_project')
        response = self.api_client.post(
            url,
            data={
                'original_query': term,
                'sortby': 'total_investment:desc',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [
            ('Ether 1', 1000),
            ('Ether 2', None),
        ] == [
            (investment['name'], investment['total_investment'])
            for investment in response.data['results']
        ]

    def test_basic_search_aggregations(self, setup_es, setup_data):
        """Tests basic aggregate query."""
        company = CompanyFactory(name='very_unique_company')
        ContactFactory(company=company)
        InvestmentProjectFactory(investor_company=company)

        setup_es.indices.refresh()

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
    def test_basic_search_permissions(self, setup_es, permission, permission_entity, entity):
        """Tests model permissions enforcement in basic search."""
        user = create_test_user(permission_codenames=[permission], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)

        InvestmentProjectFactory(created_by=user)
        CompanyFactory()
        ContactFactory()
        EventFactory()
        CompanyInteractionFactory()
        OrderFactory()

        setup_es.indices.refresh()

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

    def test_basic_search_no_permissions(self, setup_es):
        """Tests model permissions enforcement in basic search for a user with no permissions."""
        user = create_test_user(permission_codenames=[], dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)

        InvestmentProjectFactory(created_by=user)
        CompanyFactory()
        ContactFactory()
        EventFactory()
        CompanyInteractionFactory()
        OrderFactory()

        setup_es.indices.refresh()

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


class TestSearchExportAPIView(APITestMixin):
    """Tests for SearchExportAPIView."""

    def test_creates_user_event_log_entries(self, setup_es):
        """Tests that when an export is performed, a user event is recorded."""
        user = create_test_user(permission_codenames=['view_simplemodel'])
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:search:simplemodel-export')

        simple_obj = SimpleModel(name='test')
        simple_obj.save()
        sync_object_async(ESSimpleModel, SimpleModel, simple_obj.pk)

        setup_es.indices.refresh()

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
