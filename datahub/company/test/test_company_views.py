from unittest import mock

from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status

from datahub.company import models
from datahub.company.models import Company
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.core.utils import model_to_dictionary
from .factories import CompaniesHouseCompanyFactory, CompanyFactory


class CompanyTestCase(LeelooTestCase):
    """Company test case."""

    def test_list_companies(self):
        """List the companies."""
        CompanyFactory()
        CompanyFactory()
        url = reverse('company-list')
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
            registered_address_country_id=constants.Country.united_states.value.id
        )
        company = CompanyFactory(
            company_number=123,
            name='Bar ltd.',
            alias='Xyz trading'
        )

        url = reverse('company-detail', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['companies_house_data']
        assert response.data['companies_house_data']['id'] == ch_company.id
        assert response.data['name'] == ch_company.name
        assert response.data['trading_name'] == company.alias
        assert response.data['registered_address_1'] == ch_company.registered_address_1
        assert response.data['registered_address_2'] is None
        assert response.data['registered_address_3'] is None
        assert response.data['registered_address_4'] is None
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
            registered_address_country_id=constants.Country.united_states.value.id
        )

        url = reverse('company-detail', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['companies_house_data'] is None
        assert response.data['name'] == company.name
        assert response.data['registered_address_1'] == company.registered_address_1
        assert response.data['registered_address_2'] is None
        assert response.data['registered_address_3'] is None
        assert response.data['registered_address_4'] is None
        assert response.data['registered_address_town'] == company.registered_address_town
        assert response.data['registered_address_country'] == {
            'name': company.registered_address_country.name,
            'id': str(company.registered_address_country.pk)
        }
        assert response.data['registered_address_county'] is None
        assert response.data['registered_address_postcode'] is None

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    @freeze_time('2017-01-27 12:00:01')
    def test_update_company(self, mocked_save_to_korben):
        """Test company update."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=constants.Country.united_states.value.id
        )

        # now update it
        url = reverse('company-detail', kwargs={'pk': company.pk})
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            response = self.api_client.patch(url, {
                'name': 'Acme',
            })

            assert response.status_code == status.HTTP_200_OK
            assert response.data['name'] == 'Acme'
            # make sure we're spawning a task to save to Korben
            expected_data = company.convert_model_to_korben_format()
            expected_data['name'] = 'Acme'
            mocked_save_to_korben.delay.assert_called_once_with(
                db_table='company_company',
                data=expected_data,
                update=True,  # this is an update!
                user_id=self.user.id
            )
            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_uk_company(self, mocked_save_to_korben):
        """Test add new UK company."""
        url = reverse('company-list')
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            response = self.api_client.post(url, {
                'name': 'Acme',
                'alias': None,
                'business_type': constants.BusinessType.company.value.id,
                'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_country': constants.Country.united_kingdom.value.id,
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': constants.UKRegion.england.value.id
            })

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['name'] == 'Acme'
            company = Company.objects.get(pk=response.data['id'])
            expected_data = company.convert_model_to_korben_format()
            mocked_save_to_korben.delay.assert_called_once_with(
                db_table='company_company',
                data=expected_data,
                update=False,
                user_id=self.user.id
            )
            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_uk_company_without_uk_region(self, mocked_save_to_korben):
        """Test add new UK without UK region company."""
        url = reverse('company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': constants.BusinessType.company.value.id,
            'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': constants.Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
        })

        assert mocked_save_to_korben.delay.called is False
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {'uk_region': ['UK region is required for UK companies.']}

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_not_uk_company(self, mocked_save_to_korben):
        """Test add new not UK company."""
        url = reverse('company-list')
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            response = self.api_client.post(url, {
                'name': 'Acme',
                'alias': None,
                'business_type': constants.BusinessType.company.value.id,
                'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_country': constants.Country.united_states.value.id,
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
            })

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['name'] == 'Acme'
            # make sure we're spawning a task to save to Korben
            company = Company.objects.get(pk=response.data['id'])
            expected_data = company.convert_model_to_korben_format()
            mocked_save_to_korben.delay.assert_called_once_with(
                db_table='company_company',
                data=expected_data,
                update=False,
                user_id=self.user.id
            )
            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_company_partial_trading_address(self, mocked_save_to_korben):
        """Test add new company with partial trading address."""
        url = reverse('company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'business_type': constants.BusinessType.company.value.id,
            'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': constants.Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_1': 'test',
            'uk_region': constants.UKRegion.england.value.id
        })

        assert mocked_save_to_korben.delay.called is False
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['errors'] == {
            'trading_address_town': ['This field may not be null.'],
            'trading_address_country': ['This field may not be null.']
        }

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_company_with_trading_address(self, mocked_save_to_korben):
        """Test add new company with trading_address."""
        url = reverse('company-list')
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            response = self.api_client.post(url, {
                'name': 'Acme',
                'business_type': constants.BusinessType.company.value.id,
                'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_country': constants.Country.united_kingdom.value.id,
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'trading_address_country': constants.Country.ireland.value.id,
                'trading_address_1': '1 Hello st.',
                'trading_address_town': 'Dublin',
                'uk_region': constants.UKRegion.england.value.id
            })

            assert response.status_code == status.HTTP_201_CREATED
            # make sure we're spawning a task to save to Korben
            company = Company.objects.get(pk=response.data['id'])
            expected_data = company.convert_model_to_korben_format()
            mocked_save_to_korben.delay.assert_called_once_with(
                db_table='company_company',
                data=expected_data,
                update=False,
                user_id=self.user.id
            )
            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    @mock.patch('datahub.core.viewsets.tasks.save_to_korben')
    def test_add_company_with_website_without_scheme(self, mocked_save_to_korben):
        """Test add new company with trading_address."""
        url = reverse('company-list')
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            response = self.api_client.post(url, {
                'name': 'Acme',
                'business_type': constants.BusinessType.company.value.id,
                'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_country': constants.Country.united_kingdom.value.id,
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'trading_address_country': constants.Country.ireland.value.id,
                'trading_address_1': '1 Hello st.',
                'trading_address_town': 'Dublin',
                'uk_region': constants.UKRegion.england.value.id,
                'website': 'www.google.com',
            })

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['website'] == 'www.google.com'
            # make sure we're spawning a task to save to Korben
            company = Company.objects.get(pk=response.data['id'])
            expected_data = company.convert_model_to_korben_format()
            mocked_save_to_korben.delay.assert_called_once_with(
                db_table='company_company',
                data=expected_data,
                update=False,
                user_id=self.user.id
            )
            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    def test_archive_company_no_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            url = reverse('company-archive', kwargs={'pk': company.id})
            response = self.api_client.post(url, format='json')

            assert response.data['archived']
            assert response.data['archived_reason'] == ''
            assert response.data['id'] == str(company.id)

            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    def test_archive_company_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('company-archive', kwargs={'pk': company.id})
        with mock.patch('datahub.core.viewsets.tasks.save_to_es') as es_save:
            response = self.api_client.post(url, {'reason': 'foo'}, format='json')

            assert response.data['archived']
            assert response.data['archived_reason'] == 'foo'
            assert response.data['id'] == str(company.id)

            # make sure we're writing to ES
            company.refresh_from_db()
            expected_es_data = model_to_dictionary(company)
            es_save.delay.assert_called_with(
                doc_type='company_company',
                data=expected_es_data,
            )

    def test_unarchive_company(self):
        """Unarchive a company."""
        company = CompanyFactory(archived=True, archived_on=now(), archived_reason='foo')
        url = reverse('company-unarchive', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(company.id)


class CHCompanyTestCase(LeelooTestCase):
    """Companies house company test case."""

    def test_list_ch_companies(self):
        """List the companies house companies."""
        CompaniesHouseCompanyFactory()
        CompaniesHouseCompanyFactory()

        url = reverse('companieshousecompany-list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == models.CompaniesHouseCompany.objects.all().count()

    def test_detail_ch_company(self):
        """Test companies house company detail."""
        ch_company = CompaniesHouseCompanyFactory(company_number=123)

        url = reverse('companieshousecompany-detail', kwargs={'pk': ch_company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == ch_company.id

    def test_ch_company_cannot_be_written(self):
        """Test CH company POST is not allowed."""
        url = reverse('companieshousecompany-list')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_promote_a_ch_company(self):
        """Promote a CH company to full company, ES should be updated correctly."""
        CompaniesHouseCompanyFactory(company_number=1234567890)

        # promote a company to ch
        url = reverse('company-list')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'company_number': 1234567890,
            'business_type': constants.BusinessType.company.value.id,
            'sector': constants.Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': constants.Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': constants.Country.ireland.value.id,
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': constants.UKRegion.england.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
