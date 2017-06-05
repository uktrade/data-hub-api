from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.constants import (BusinessType, CompanyClassification, 
                                    Country,  HeadquarterType, Sector, 
                                    UKRegion)
from datahub.core.test_utils import LeelooTestCase
from .factories import CompanyFactory


class CompanyTestCase(LeelooTestCase):
    """Company test case."""

    def test_list_companies(self):
        """List the companies."""
        CompanyFactory()
        CompanyFactory()
        url = reverse('api-v3:company:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_update_company(self):
        """Test company update."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id
        )

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, format='json', data={
            'name': 'Acme',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Acme'

    def test_add_uk_company(self):
        """Test add new UK company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'alias': None,
            'business_type': {'id': BusinessType.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_kingdom.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'uk_region': {'id': UKRegion.england.value.id},
            'headquarter_type': {'id': HeadquarterType.ghq.value.id},
            'classification': {'id': CompanyClassification.tier_a.value.id},
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'

    def test_add_uk_company_without_uk_region(self):
        """Test add new UK without UK region company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'alias': None,
            'business_type': {'id': BusinessType.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_kingdom.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {'uk_region': ['UK region is required for UK companies.']}

    def test_add_not_uk_company(self):
        """Test add new not UK company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'alias': None,
            'business_type': {'id': BusinessType.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_states.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'

    def test_add_company_partial_trading_address(self):
        """Test add new company with partial trading address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'business_type': {'id': BusinessType.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_kingdom.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_1': 'test',
            'uk_region': {'id': UKRegion.england.value.id}
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'trading_address_town': ['This field may not be null.'],
            'trading_address_country': ['This field may not be null.']
        }

    def test_add_company_with_trading_address(self):
        """Test add new company with trading_address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'business_type': {'id': BusinessType.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_kingdom.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': {'id': Country.ireland.value.id},
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': {'id': UKRegion.england.value.id}
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_company_with_website_without_scheme(self):
        """Test add new company with trading_address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'business_type': {'id': BusinessType.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_kingdom.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': {'id': Country.ireland.value.id},
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': {'id': UKRegion.england.value.id},
            'website': 'www.google.com',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['website'] == 'www.google.com'
