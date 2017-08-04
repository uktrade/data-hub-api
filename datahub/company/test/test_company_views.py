from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company import models
from datahub.core.constants import (
    BusinessType, CompanyClassification, Country, HeadquarterType, Sector, UKRegion
)
from datahub.core.test_utils import APITestMixin
from datahub.interaction.test.factories import InteractionFactory
from .factories import CompaniesHouseCompanyFactory, CompanyFactory


class TestCompany(APITestMixin):
    """Company test case."""

    def test_list_companies(self):
        """List the companies."""
        CompanyFactory()
        CompanyFactory()
        url = reverse('api-v1:company-list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_detail_company_with_company_number(self):
        """Test company detail view with companies house data.

        Make sure that the registered name and registered address are coming from CH data
        """
        ch_company = CompaniesHouseCompanyFactory(
            company_number=123,
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id
        )
        company = CompanyFactory(
            company_number=123,
            name='Bar ltd.',
            alias='Xyz trading'
        )

        url = reverse('api-v1:company-detail', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['created_by']['id'] == str(company.created_by.id)
        assert response.data['modified_by']['id'] == str(company.modified_by.id)
        assert response.data['companies_house_data']
        assert response.data['companies_house_data']['id'] == ch_company.id
        assert response.data['name'] == ch_company.name
        assert response.data['trading_name'] == company.alias
        assert response.data['registered_address_1'] == ch_company.registered_address_1
        assert response.data['registered_address_2'] is None
        assert response.data['registered_address_town'] == ch_company.registered_address_town
        assert response.data['registered_address_country'] == {
            'name': ch_company.registered_address_country.name,
            'id': str(ch_company.registered_address_country.pk)
        }
        assert response.data['registered_address_county'] is None
        assert response.data['registered_address_postcode'] is None

    def test_detail_company_without_company_number(self):
        """Test company detail view without companies house data.

        Make sure that the registered name and address are coming from CDMS.
        """
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
            headquarter_type_id=HeadquarterType.ukhq.value.id,
            classification_id=CompanyClassification.tier_a.value.id,
        )

        url = reverse('api-v1:company-detail', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['created_by']['id'] == str(company.created_by.id)
        assert response.data['modified_by']['id'] == str(company.modified_by.id)
        assert response.data['companies_house_data'] is None
        assert response.data['name'] == company.name
        assert response.data['registered_address_1'] == company.registered_address_1
        assert response.data['registered_address_2'] is None
        assert response.data['registered_address_town'] == company.registered_address_town
        assert response.data['registered_address_country'] == {
            'name': company.registered_address_country.name,
            'id': str(company.registered_address_country.pk)
        }
        assert response.data['registered_address_county'] is None
        assert response.data['registered_address_postcode'] is None
        assert response.data['headquarter_type']['name'] == HeadquarterType.ukhq.value.name
        assert response.data['classification']['name'] == CompanyClassification.tier_a.value.name

    def test_detail_company_adviser_not_expanded(self):
        """Tests that advisers are not expanded in the interactions list.

        Avoids repeating a regression where it was accidentally amended to be expanded.
        """
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
            headquarter_type_id=HeadquarterType.ukhq.value.id,
            classification_id=CompanyClassification.tier_a.value.id,
        )
        interaction = InteractionFactory(company=company)

        url = reverse('api-v1:company-detail', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['interactions'][0]['dit_adviser'] == str(interaction.dit_adviser.pk)

    def test_update_company(self):
        """Test company update."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id
        )

        # now update it
        url = reverse('api-v1:company-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, {
            'name': 'Acme',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Acme'
        assert response.data['modified_by'] == self.user.id

    def test_classification_is_ro(self):
        """Test that classification is fail-safe & read-only."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
            classification_id=CompanyClassification.tier_a.value.id,
        )

        url = reverse('api-v1:company-detail', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, {
            'classification': CompanyClassification.tier_b.value.id,
        })

        assert response.status_code == 200  # testing that this should be silently ignored error
        company.refresh_from_db()
        assert str(company.classification_id) == CompanyClassification.tier_a.value.id

    def test_add_uk_company(self):
        """Test add new UK company."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'uk_region': UKRegion.england.value.id,
            'headquarter_type': HeadquarterType.ghq.value.id,
            'classification': CompanyClassification.tier_a.value.id,
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'

    def test_add_uk_company_without_uk_region(self):
        """Test add new UK without UK region company."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'uk_region': ['UK region is required for UK companies.']
        }

    def test_add_not_uk_company(self):
        """Test add new not UK company."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_states.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'

    def test_add_company_partial_trading_address(self):
        """Test add new company with partial trading address."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_1': 'test',
            'uk_region': UKRegion.england.value.id
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'trading_address_town': ['This field may not be null.'],
            'trading_address_country': ['This field may not be null.']
        }

    def test_add_company_with_trading_address(self):
        """Test add new company with trading_address."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': Country.ireland.value.id,
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': UKRegion.england.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_company_without_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field is required.'],
            'registered_address_town': ['This field is required.'],
            'registered_address_country': ['This field is required.']
        }

    def test_add_company_with_null_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_1': None,
            'registered_address_town': None,
            'registered_address_country': None,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field may not be null.'],
            'registered_address_town': ['This field may not be null.'],
            'registered_address_country': ['This field may not be null.']
        }

    def test_add_company_with_blank_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_1': '',
            'registered_address_town': '',
            'registered_address_country': None,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field may not be blank.'],
            'registered_address_town': ['This field may not be blank.'],
            'registered_address_country': ['This field may not be null.']
        }

    def test_add_company_with_website_without_scheme(self):
        """Test add new company with trading_address."""
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': Country.ireland.value.id,
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': UKRegion.england.value.id,
            'website': 'www.google.com',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['website'] == 'www.google.com'

    def test_archive_company_no_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v1:company-archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.']
        }

    def test_archive_company_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v1:company-archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, {'reason': 'foo'}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == str(company.id)

    def test_unarchive_company(self):
        """Unarchive a company."""
        company = CompanyFactory(archived=True, archived_on=now(), archived_reason='foo')
        url = reverse('api-v1:company-unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(company.id)

    def test_unarchive_wrong_method(self):
        """Tests that GET requests to the unarchive endpoint fail."""
        company = CompanyFactory(archived=True, archived_on=now(), archived_reason='foo')
        url = reverse('api-v1:company-unarchive', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestCHCompany(APITestMixin):
    """Companies house company test case."""

    def test_list_ch_companies(self):
        """List the companies house companies."""
        CompaniesHouseCompanyFactory()
        CompaniesHouseCompanyFactory()

        url = reverse('api-v1:companieshousecompany-list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == models.CompaniesHouseCompany.objects.all().count()

    def test_detail_ch_company(self):
        """Test companies house company detail."""
        ch_company = CompaniesHouseCompanyFactory(company_number=123)

        url = reverse('api-v1:companieshousecompany-detail', kwargs={
            'company_number': ch_company.company_number
        })
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == ch_company.id

    def test_ch_company_cannot_be_written(self):
        """Test CH company POST is not allowed."""
        url = reverse('api-v1:companieshousecompany-list')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_promote_a_ch_company(self):
        """Promote a CH company to full company, ES should be updated correctly."""
        CompaniesHouseCompanyFactory(company_number=1234567890)

        # promote a company to ch
        url = reverse('api-v1:company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'company_number': 1234567890,
            'business_type': BusinessType.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': Country.ireland.value.id,
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': UKRegion.england.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
