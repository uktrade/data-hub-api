import uuid

import factory
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Country, Sector, UKRegion
from datahub.core.test_utils import APITestMixin, create_test_user, random_obj_for_queryset
from datahub.metadata.models import Sector as SectorModel
from datahub.metadata.test.factories import TeamFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_data():
    """Sets up data for the tests."""
    contacts = [
        ContactFactory(first_name='abc', last_name='defg'),
        ContactFactory(first_name='first', last_name='last')
    ]
    yield contacts


class TestSearch(APITestMixin):
    """Tests search views."""

    def test_company_search_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:search:contact')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_search_contact(self, setup_es, setup_data):
        """Tests detailed contact search."""
        setup_es.indices.refresh()

        term = 'abc defg'

        url = reverse('api-v3:search:contact')

        united_kingdom_id = Country.united_kingdom.value.id

        response = self.api_client.post(url, {
            'original_query': term,
            'address_country': united_kingdom_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0
        contact = response.data['results'][0]
        assert contact['address_country']['id'] == united_kingdom_id

    def test_filter_contact(self, setup_es):
        """Tests matching contact using multiple filters."""
        contact = ContactFactory(address_same_as_company=True)
        company = contact.company
        company.name = 'SlothsCats'
        company.trading_address_country_id = Country.united_kingdom.value.id
        company.uk_region_id = UKRegion.east_of_england.value.id
        company.sector_id = Sector.renewable_energy_wind.value.id
        company.save()

        setup_es.indices.refresh()

        term = ''

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'original_query': term,
            'company_name': company.name,
            'company_sector': company.sector_id,
            'company_uk_region': company.uk_region_id,
            'address_country': company.trading_address_country_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        contact = response.data['results'][0]
        assert contact['address_country']['id'] == company.trading_address_country_id
        assert contact['company']['name'] == company.name
        assert contact['company_uk_region']['id'] == company.uk_region_id
        assert contact['company_sector']['id'] == company.sector_id

    def test_filter_without_uk_region(self, setup_es):
        """Tests matching contact without uk_region using multiple filters."""
        company = CompanyFactory(
            registered_address_country_id=Country.united_states.value.id,
            trading_address_country_id=Country.united_states.value.id,
            uk_region_id=None,
            sector_id=Sector.renewable_energy_wind.value.id
        )
        ContactFactory(
            address_same_as_company=True,
            company=company
        )

        setup_es.indices.refresh()

        term = ''

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'original_query': term,
            'company_name': company.name,
            'company_sector': company.sector_id,
            'address_country': company.trading_address_country_id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        contact = response.data['results'][0]
        assert contact['address_country']['id'] == company.trading_address_country_id
        assert contact['company']['name'] == company.name
        assert contact['company_uk_region'] is None
        assert contact['company_sector']['id'] == company.sector_id

    @pytest.mark.parametrize(
        'sector_level',
        (0, 1, 2),
    )
    def test_company_sector_descends_filter(self, hierarchical_sectors, setup_es, sector_level):
        """Test the company_sector_descends filter."""
        num_sectors = len(hierarchical_sectors)
        sectors_ids = [sector.pk for sector in hierarchical_sectors]

        companies = CompanyFactory.create_batch(
            num_sectors,
            sector_id=factory.Iterator(sectors_ids)
        )
        contacts = ContactFactory.create_batch(
            3,
            company=factory.Iterator(companies)
        )

        other_companies = CompanyFactory.create_batch(
            3,
            sector=factory.LazyFunction(lambda: random_obj_for_queryset(
                SectorModel.objects.exclude(pk__in=sectors_ids)
            ))
        )
        ContactFactory.create_batch(
            3,
            company=factory.Iterator(other_companies)
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')
        body = {
            'company_sector_descends': hierarchical_sectors[sector_level].pk
        }
        response = self.api_client.post(url, body)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == num_sectors - sector_level

        actual_ids = {uuid.UUID(contact['id']) for contact in response_data['results']}
        expected_ids = {contact.pk for contact in contacts[sector_level:]}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'term,match',
        (
            ('whiskers', True),
            ('house lion', True),
            ('tiger', False),
            ('panda', False),
        )
    )
    def test_search_contact_by_partial_company_name(self, setup_es, term, match):
        """Tests filtering by partially matching company name."""
        matching_company = CompanyFactory(
            name='whiskers and tabby',
            alias='house lion and moggie',
        )
        non_matching_company = CompanyFactory(
            name='Pluto and pippo',
            alias='Epsilon and lippo',
        )
        matching_contact = ContactFactory(company=matching_company)
        ContactFactory(company=non_matching_company)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'original_query': '',
            'company_name': term,
        })

        assert response.status_code == status.HTTP_200_OK
        if match:
            assert response.data['count'] == 1
            assert len(response.data['results']) == 1
            assert response.data['results'][0]['id'] == str(matching_contact.id)
        else:
            assert response.data['count'] == 0
            assert len(response.data['results']) == 0

    def test_search_contact_by_partial_name(self, setup_es, setup_data):
        """Tests filtering by partially matching name."""
        contact = ContactFactory(first_name='xyzxyz')

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'name': 'xyz',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['first_name'] == contact.first_name

    @pytest.mark.parametrize(
        'archived', (
            True,
            False,
        )
    )
    def test_search_contact_by_archived(self, setup_es, setup_data, archived):
        """Tests filtering by archived."""
        ContactFactory.create_batch(5, archived=True)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'archived': archived,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] > 0
        assert all(result['archived'] == archived for result in response.data['results'])

    @pytest.mark.parametrize(
        'created_on_exists',
        (True, False)
    )
    def test_filter_by_created_on_exists(self, setup_es, created_on_exists):
        """Tests filtering contact by created_on exists."""
        ContactFactory.create_batch(3)
        no_created_on = ContactFactory.create_batch(3)
        for contact in no_created_on:
            contact.created_on = None
            contact.save()

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')
        request_data = {
            'created_on_exists': created_on_exists,
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        results = response_data['results']
        assert response_data['count'] == 3
        assert all((not result['created_on'] is None) == created_on_exists
                   for result in results)

    def test_search_contact_by_company_id(self, setup_es, setup_data):
        """Tests filtering by company id."""
        company = CompanyFactory()
        ContactFactory(company=company)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'company': company.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['company']['id'] == str(company.id)

    def test_search_contact_by_created_by(self, setup_es, setup_data):
        """Tests filtering by created_by."""
        adviser = AdviserFactory()
        ContactFactory(created_by=adviser)

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'created_by': adviser.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['created_by']['id'] == str(adviser.id)

    def test_company_name_trigram_filter(self, setup_es):
        """Tests edge case of partially matching company name."""
        company = CompanyFactory(name='United States')
        ContactFactory(
            company=company
        )
        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')

        response = self.api_client.post(url, {
            'company_name': 'scared Squirrel',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0

    def test_search_contact_no_filters(self, setup_es, setup_data):
        """Tests case where there is no filters provided."""
        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_search_contact_sort_by_last_name_desc(self, setup_es):
        """Tests sorting in descending order."""
        ContactFactory(first_name='test_name', last_name='abcdef')
        ContactFactory(first_name='test_name', last_name='bcdefg')
        ContactFactory(first_name='test_name', last_name='cdefgh')
        ContactFactory(first_name='test_name', last_name='defghi')

        setup_es.indices.refresh()

        term = 'test_name'

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'last_name:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4
        assert ['defghi',
                'cdefgh',
                'bcdefg',
                'abcdef'] == [contact['last_name'] for contact in response.data['results']]

    def test_search_contact_sort_by_company_sector_desc(self, setup_es):
        """Tests sorting by company_sector in descending order."""
        company1 = CompanyFactory(
            sector_id=Sector.renewable_energy_wind.value.id,
        )
        company2 = CompanyFactory(
            sector_id=Sector.aerospace_assembly_aircraft.value.id,
        )

        ContactFactory(
            first_name='61409aa1fd47d4a5',
            company=company1
        )
        ContactFactory(
            first_name='61409aa1fd47d4a5',
            company=company2
        )

        setup_es.indices.refresh()

        term = '61409aa1fd47d4a5'

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': term,
            'sortby': 'company_sector.name:desc',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert [company1.sector.id,
                company2.sector.id] == [uuid.UUID(contact['company_sector']['id'])
                                        for contact in response.data['results']]


class TestBasicSearch(APITestMixin):
    """Tests basic search view."""

    def test_basic_search_contacts(self, setup_es, setup_data):
        """Tests basic aggregate contacts query."""
        setup_es.indices.refresh()

        term = 'abc defg'

        url = reverse('api-v3:search:basic')
        response = self.api_client.get(url, {
            'term': term,
            'entity': 'contact'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['first_name'] in term
        assert response.data['results'][0]['last_name'] in term
        assert [{'count': 1, 'entity': 'contact'}] == response.data['aggregations']

    def test_search_contact_has_sector(self, setup_es, setup_data):
        """Tests if contact has a sector."""
        ContactFactory(first_name='sector_testing')

        setup_es.indices.refresh()

        term = 'sector_testing'

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': term,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        sector_name = Sector.aerospace_assembly_aircraft.value.name
        assert sector_name == response.data['results'][0]['company_sector']['name']

    def test_search_contact_has_sector_updated(self, setup_es):
        """Tests if contact has a correct sector after company update."""
        contact = ContactFactory(first_name='sector_update')

        # by default company has aerospace_assembly_aircraft sector assigned
        company = contact.company
        company.sector_id = Sector.renewable_energy_wind.value.id
        company.save()

        setup_es.indices.refresh()

        term = 'sector_update'

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': term,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        sector_name = Sector.renewable_energy_wind.value.name
        assert sector_name == response.data['results'][0]['company_sector']['name']

    def test_search_contact_has_company_trading_address_updated(self, setup_es):
        """Tests if contact has a correct address after company trading address update."""
        contact = ContactFactory(
            address_same_as_company=True
        )

        address = {
            'address_1': '1 Own Street',
            'address_2': '',
            'address_county': 'Hello',
            'address_town': 'Super Town',
            'address_postcode': 'ABC DEF',
        }

        company = contact.company
        for k, v in address.items():
            setattr(company, f'trading_{k}', v)
        company.trading_address_country.id = Country.united_kingdom.value.id
        company.save()

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': contact.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        result = response.data['results'][0]

        for k, v in address.items():
            assert v == result[k]

        country = contact.company.trading_address_country.name
        assert country == result['address_country']['name']

    def test_search_contact_has_company_registered_address_updated(self, setup_es):
        """Tests if contact has a correct address after company registered address update."""
        contact = ContactFactory(
            address_same_as_company=True
        )

        address = {
            'address_1': '2 Own Street',
            'address_2': '',
            'address_county': 'Hello',
            'address_town': 'Cats Town',
            'address_postcode': 'ABC DEF',
        }

        company = contact.company
        for k, v in address.items():
            setattr(company, f'registered_{k}', v)
            setattr(company, f'trading_{k}', None)
        company.registered_address_country.id = Country.united_kingdom.value.id
        company.trading_address_country = None
        company.save()

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': contact.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        result = response.data['results'][0]

        for k, v in address.items():
            assert v == result[k]

        country = contact.company.registered_address_country.name
        assert country == result['address_country']['name']

    def test_search_contact_has_own_address(self, setup_es):
        """Tests if contact can have its own address."""
        address = {
            'address_same_as_company': False,
            'address_1': 'Own Street',
            'address_2': '',
            'address_town': 'Super Town',
        }

        contact = ContactFactory(
            address_country_id=Country.united_kingdom.value.id,
            **address
        )

        setup_es.indices.refresh()

        url = reverse('api-v3:search:contact')
        response = self.api_client.post(url, {
            'original_query': contact.id,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

        result = response.data['results'][0]

        for k, v in address.items():
            assert v == result[k]

        assert contact.address_country.name == result['address_country']['name']
