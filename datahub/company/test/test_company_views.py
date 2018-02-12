from operator import itemgetter

import pytest
import reversion
from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import CompaniesHouseCompany
from datahub.company.test.factories import CompaniesHouseCompanyFactory, CompanyFactory
from datahub.core.constants import (
    CompanyClassification, Country, HeadquarterType, Sector, UKRegion
)
from datahub.core.test_utils import APITestMixin, create_test_user, format_date_or_datetime
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory


class TestListCompanies(APITestMixin):
    """Tests for listing companies."""

    def test_companies_list_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:company:collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_companies(self):
        """List the companies."""
        CompanyFactory.create_batch(2)
        url = reverse('api-v3:company:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_list_companies_without_read_document_permission(self):
        """List the companies by user without read document permission."""
        CompanyFactory.create_batch(5, archived_documents_url_path='hello world')

        user = create_test_user(
            permission_codenames=(
                'read_company',
            )
        )
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:company:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert all(
            'archived_documents_url_path' not in company
            for company in response.data['results']
        )

    def test_list_companies_with_read_document_permission(self):
        """List the companies by user with read document permission."""
        CompanyFactory.create_batch(5, archived_documents_url_path='hello world')

        user = create_test_user(
            permission_codenames=(
                'read_company',
                'read_company_document',
            )
        )
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:company:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert all(
            company['archived_documents_url_path'] == 'hello world'
            for company in response.data['results']
        )


class TestGetCompany(APITestMixin):
    """Tests for getting a company."""

    def test_get_company_without_read_document_permission(self):
        """Tests the company item view without read document permission."""
        company = CompanyFactory(
            archived_documents_url_path='http://some-documents',
        )
        user = create_test_user(
            permission_codenames=(
                'read_company',
            )
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'archived_documents_url_path' not in response.json()

    def test_get_company_with_company_number(self):
        """Tests the company item view for a company with a company number."""
        ch_company = CompaniesHouseCompanyFactory(
            company_number=123,
            name='Foo Ltd',
            registered_address_1='Hello St',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id
        )
        company = CompanyFactory(
            company_number=123,
            name='Bar Ltd',
            alias='Xyz trading',
            vat_number='009485769',
            registered_address_1='Goodbye St',
            registered_address_town='Barland',
            registered_address_country_id=Country.united_kingdom.value.id
        )
        user = create_test_user(
            permission_codenames=(
                'read_company',
                'read_company_document',
            )
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(company.pk),
            'companies_house_data': {
                'id': ch_company.id,
                'company_number': '123',
                'company_category': '',
                'company_status': '',
                'incorporation_date': format_date_or_datetime(ch_company.incorporation_date),
                'name': 'Foo Ltd',
                'registered_address_1': 'Hello St',
                'registered_address_2': None,
                'registered_address_town': 'Fooland',
                'registered_address_county': None,
                'registered_address_postcode': None,
                'registered_address_country': {
                    'id': str(ch_company.registered_address_country.id),
                    'disabled_on': None,
                    'name': ch_company.registered_address_country.name,
                },
                'sic_code_1': '',
                'sic_code_2': '',
                'sic_code_3': '',
                'sic_code_4': '',
                'uri': '',
            },
            'reference_code': '',
            'name': 'Bar Ltd',
            'trading_name': 'Xyz trading',
            'registered_address_1': 'Goodbye St',
            'registered_address_2': None,
            'registered_address_town': 'Barland',
            'registered_address_county': None,
            'registered_address_postcode': None,
            'registered_address_country': {
                'id': str(Country.united_kingdom.value.id),
                'name': Country.united_kingdom.value.name,
            },
            'account_manager': None,
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': company.archived_documents_url_path,
            'archived_on': None,
            'archived_reason': None,
            'business_type': {
                'id': str(company.business_type.id),
                'name': company.business_type.name,
            },
            'children': [],
            'subsidiaries': [],
            'classification': None,
            'company_number': '123',
            'contacts': [],
            'created_on': format_date_or_datetime(company.created_on),
            'description': None,
            'employee_range': None,
            'export_experience_category': {
                'id': str(company.export_experience_category.id),
                'name': company.export_experience_category.name,
            },
            'export_to_countries': [],
            'future_interest_countries': [],
            'headquarter_type': None,
            'investment_projects_invested_in': [],
            'investment_projects_invested_in_count': 0,
            'modified_on': format_date_or_datetime(company.modified_on),
            'one_list_account_owner': None,
            'parent': None,
            'global_headquarter': None,
            'sector': {
                'id': str(company.sector.id),
                'name': company.sector.name,
            },
            'trading_address_1': company.trading_address_1,
            'trading_address_2': None,
            'trading_address_country': {
                'id': str(company.trading_address_country.id),
                'name': company.trading_address_country.name
            },
            'trading_address_county': None,
            'trading_address_postcode': None,
            'trading_address_town': 'Woodside',
            'turnover_range': None,
            'uk_based': True,
            'uk_region': {
                'id': str(company.uk_region.id),
                'name': company.uk_region.name,
            },
            'vat_number': '009485769',
            'website': None,
        }

    def test_get_company_without_company_number(self):
        """Tests the company item view for a company without a company number.

        Checks that that the registered name and address are coming from the
        company record.
        """
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
            headquarter_type_id=HeadquarterType.ukhq.value.id,
            classification_id=CompanyClassification.tier_a.value.id,
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['companies_house_data'] is None
        assert response.data['name'] == company.name
        assert (response.data['registered_address_1'] ==
                company.registered_address_1)
        assert response.data['registered_address_2'] is None
        assert (response.data['registered_address_town'] ==
                company.registered_address_town)
        assert response.data['registered_address_country'] == {
            'name': company.registered_address_country.name,
            'id': str(company.registered_address_country.pk)
        }
        assert response.data['registered_address_county'] is None
        assert response.data['registered_address_postcode'] is None
        assert (response.data['headquarter_type']['id'] ==
                HeadquarterType.ukhq.value.id)
        assert (response.data['classification']['id'] ==
                CompanyClassification.tier_a.value.id)

    def test_get_company_without_registered_country(self):
        """Tests the company item view for a company without a registered
        company.

        Checks that the endpoint returns 200 and the uk_based attribute is
        set to None.
        """
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=None,
            headquarter_type_id=HeadquarterType.ukhq.value.id,
            classification_id=CompanyClassification.tier_a.value.id,
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['uk_based'] is None

    def test_get_company_investment_projects(self):
        """Tests investment project properties in the company item view."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
            headquarter_type_id=HeadquarterType.ukhq.value.id,
            classification_id=CompanyClassification.tier_a.value.id,
        )
        projects = InvestmentProjectFactory.create_batch(
            3, investor_company_id=company.id
        )
        InvestmentProjectFactory.create_batch(
            2, intermediate_company_id=company.id
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['id'] == str(company.pk)
        actual_projects = sorted(
            response_data['investment_projects_invested_in'],
            key=itemgetter('id')
        )
        expected_projects = sorted(({
            'id': str(projects[0].id),
            'name': projects[0].name,
            'project_code': projects[0].project_code
        }, {
            'id': str(projects[1].id),
            'name': projects[1].name,
            'project_code': projects[1].project_code
        }, {
            'id': str(projects[2].id),
            'name': projects[2].name,
            'project_code': projects[2].project_code
        }), key=itemgetter('id'))

        assert actual_projects == expected_projects

    @pytest.mark.parametrize(
        'input_website,expected_website', (
            ('www.google.com', 'http://www.google.com'),
            ('http://www.google.com', 'http://www.google.com'),
            ('https://www.google.com', 'https://www.google.com'),
            ('', ''),
            (None, None),
        )
    )
    def test_get_company_with_website(self, input_website, expected_website):
        """Test add new company with trading_address."""
        company = CompanyFactory(
            website=input_website
        )
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['website'] == expected_website


class TestUpdateCompany(APITestMixin):
    """Tests for updating a single company."""

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

    def test_update_company_with_company_number(self):
        """
        Test updating a company that has a corresponding Companies House record.

        Updates to the name and registered address should be allowed.
        """
        CompaniesHouseCompanyFactory(
            company_number=123,
            name='Foo Ltd',
            registered_address_1='Hello St',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id
        )
        company = CompanyFactory(
            company_number=123,
            name='Bar Ltd',
            alias='Xyz trading',
            vat_number='009485769',
            registered_address_1='Goodbye St',
            registered_address_town='Barland',
            registered_address_country_id=Country.united_kingdom.value.id
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})

        update_data = {
            'name': 'New name',
            'registered_address_1': 'New address 1',
            'registered_address_town': 'New town',
            'registered_address_country': Country.united_states.value.id,
        }

        response = self.api_client.patch(url, format='json', data=update_data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == update_data['name']
        assert response.data['registered_address_1'] == update_data['registered_address_1']
        assert response.data['registered_address_town'] == update_data['registered_address_town']
        assert response.data['registered_address_country']['id'] == Country.united_states.value.id

    def test_update_read_only_fields(self):
        """Test updating read-only fields."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
            reference_code='ORG-345645',
            archived_documents_url_path='old_path',
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, format='json', data={
            'reference_code': 'XYZ',
            'archived_documents_url_path': 'new_path'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['reference_code'] == 'ORG-345645'
        assert response.data['archived_documents_url_path'] == 'old_path'

    def test_long_trading_name(self):
        """Test that providing a long trading name doesn't return a 500."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, format='json', data={
            'trading_name': 'a' * 600,
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'trading_name': ['Ensure this field has no more than 255 characters.']
        }

    @pytest.mark.parametrize('field,value', (
        ('sector', Sector.aerospace_assembly_aircraft.value.id),
    ))
    def test_update_non_null_field_to_null(self, field, value):
        """
        Tests setting fields to null that are currently non-null, and are allowed to be null
        when already null.
        """
        creation_data = {
            'name': 'Foo ltd.',
            'registered_address_1': 'Hello st.',
            'registered_address_town': 'Fooland',
            'registered_address_country_id': Country.united_states.value.id,
            f'{field}_id': value
        }
        company = CompanyFactory(**creation_data)

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, {
            field: None,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            field: ['This field is required.'],
        }

    @pytest.mark.parametrize('field', ('sector',))
    def test_update_null_field_to_null(self, field):
        """
        Tests setting fields to null that are currently null, and are allowed to be null
        when already null.
        """
        creation_data = {
            'name': 'Foo ltd.',
            'registered_address_1': 'Hello st.',
            'registered_address_town': 'Fooland',
            'registered_address_country_id': Country.united_states.value.id,
            f'{field}_id': None
        }
        company = CompanyFactory(**creation_data)

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, {
            field: None,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[field] is None

    @pytest.mark.parametrize('hq,is_valid', (
        (HeadquarterType.ehq.value.id, False),
        (HeadquarterType.ukhq.value.id, False),
        (HeadquarterType.ghq.value.id, True),
        (None, False),
    ))
    def test_update_company_global_headquarters_with_not_a_global_headquarter(self, hq, is_valid):
        """Tests if adding company that is not a Global HQ as a Global HQ
        will fail or if added company is a Global HQ then it will pass.
        """
        company = CompanyFactory()
        headquarter = CompanyFactory(headquarter_type_id=hq)

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, format='json', data={
            'global_headquarter': headquarter.id,
        })
        if is_valid:
            assert response.status_code == status.HTTP_200_OK
            if hq is not None:
                assert response.data['global_headquarter']['id'] == str(headquarter.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error = ['Company to be set as Global Headquarter must be a Global Headquarter.']
            assert response.data['global_headquarter'] == error

    def test_remove_global_headquarter_link(self):
        """Tests if we can remove global headquarter link."""
        global_headquarter = CompanyFactory(
            headquarter_type_id=HeadquarterType.ghq.value.id
        )
        company = CompanyFactory(global_headquarter=global_headquarter)

        assert global_headquarter.subsidiaries.count() == 1

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, format='json', data={
            'global_headquarter': None,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['global_headquarter'] is None

        assert global_headquarter.subsidiaries.count() == 0


class TestAddCompany(APITestMixin):
    """Tests for adding a company."""

    def test_add_uk_company(self):
        """Test add new UK company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.company.value.id},
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
        assert response.data['trading_name'] == 'Trading name'

    def test_promote_a_ch_company(self):
        """Promote a CH company to full company."""
        CompaniesHouseCompanyFactory(company_number=1234567890)

        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'company_number': 1234567890,
            'business_type': BusinessTypeConstant.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_country': Country.united_kingdom.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'trading_address_country': Country.ireland.value.id,
            'trading_address_1': '1 Hello st.',
            'trading_address_town': 'Dublin',
            'uk_region': UKRegion.england.value.id
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_uk_company_without_uk_region(self):
        """Test add new UK without UK region company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': None,
            'business_type': {'id': BusinessTypeConstant.company.value.id},
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_kingdom.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {'uk_region': ['This field is required.']}

    def test_add_not_uk_company(self):
        """Test add new not UK company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': None,
            'business_type': {'id': BusinessTypeConstant.company.value.id},
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
            'business_type': {'id': BusinessTypeConstant.company.value.id},
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
            'trading_address_town': ['This field is required.'],
            'trading_address_country': ['This field is required.']
        }

    def test_add_company_with_trading_address(self):
        """Test add new company with trading_address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'business_type': {'id': BusinessTypeConstant.company.value.id},
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

    def test_add_company_without_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'trading_name': None,
            'business_type': BusinessTypeConstant.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field is required.'],
            'registered_address_town': ['This field is required.'],
            'registered_address_country': ['This field is required.'],
        }

    def test_add_company_with_null_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'trading_name': None,
            'business_type': BusinessTypeConstant.company.value.id,
            'sector': Sector.aerospace_assembly_aircraft.value.id,
            'registered_address_1': None,
            'registered_address_town': None,
            'registered_address_country': None
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field may not be null.'],
            'registered_address_town': ['This field may not be null.'],
            'registered_address_country': ['This field may not be null.'],
        }

    def test_add_company_with_blank_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'trading_name': None,
            'business_type': BusinessTypeConstant.company.value.id,
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

    @pytest.mark.parametrize('field', ('sector',))
    def test_add_company_without_required_field(self, field):
        """
        Tests adding a company without required fields that are allowed to be null (during
        updates) when already null.
        """
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'alias': None,
            'business_type': BusinessTypeConstant.company.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'registered_address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.england.value.id,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[field] == ['This field is required.']

    @pytest.mark.parametrize(
        'input_website,expected_website', (
            ('www.google.com', 'http://www.google.com'),
            ('http://www.google.com', 'http://www.google.com'),
            ('https://www.google.com', 'https://www.google.com'),
            ('', ''),
            (None, None),
        )
    )
    def test_add_company_with_website(self, input_website, expected_website):
        """Test add new company with trading_address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'business_type': {'id': BusinessTypeConstant.company.value.id},
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
            'website': input_website,
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['website'] == expected_website

    def test_add_uk_establishment(self):
        """Test adding a UK establishment."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
            'company_number': 'BR000006',
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
        assert response.json()['company_number'] == 'BR000006'

    def test_cannot_add_uk_establishment_without_number(self):
        """Test that a UK establishment cannot be added without a company number."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
            'company_number': '',
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

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company_number': ['This field is required.']
        }

    def test_cannot_add_uk_establishment_as_foreign_company(self):
        """Test that adding a UK establishment fails if its country is not UK."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
            'company_number': 'BR000006',
            'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
            'registered_address_country': {
                'id': Country.united_states.value.id
            },
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'uk_region': {'id': UKRegion.england.value.id},
            'headquarter_type': {'id': HeadquarterType.ghq.value.id},
            'classification': {'id': CompanyClassification.tier_a.value.id},
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'registered_address_country':
                ['A UK establishment (branch of non-UK company) must be in the UK.']
        }

    def test_cannot_add_uk_establishment_invalid_prefix(self):
        """
        Test that adding a UK establishment fails if its company number does not start with BR.
        """
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
            'company_number': 'SC000006',
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

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company_number':
                ['This must be a valid UK establishment number, beginning with BR.']
        }

    def test_cannot_add_uk_establishment_invalid_characters(self):
        """
        Test that adding a UK establishment fails if its company number contains invalid
        characters.
        """
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
            'company_number': 'BR000444é',
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

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company_number':
                ['This field can only contain the letters A to Z and numbers (no symbols, '
                 'punctuation or spaces).']
        }

    def test_no_company_number_validation_for_normal_uk_companies(self):
        """Test that no validation is done on company number for normal companies."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': 'Trading name',
            'business_type': {'id': BusinessTypeConstant.private_limited_company.value.id},
            'company_number': 'sc000444é',
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
        assert response.json()['company_number'] == 'sc000444é'


class TestArchiveCompany(APITestMixin):
    """Archive company tests."""

    def test_archive_company_no_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.']
        }

    def test_archive_company_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, {'reason': 'foo'}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'
        assert response.data['id'] == str(company.id)

    def test_archive_company_invalid_address(self):
        """
        Test archiving a company when the company has an invalid trading address and missing
        UK region.
        """
        company = CompanyFactory(
            registered_address_country_id=Country.united_kingdom.value.id,
            trading_address_town='',
            uk_region_id=None,
        )
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, {'reason': 'foo'}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'


class TestUnarchiveCompany(APITestMixin):
    """Unarchive company tests."""

    def test_unarchive_company_invalid_address(self):
        """
        Test unarchiving a company when the company has an invalid trading address and missing
        UK region.
        """
        company = CompanyFactory(
            registered_address_country_id=Country.united_kingdom.value.id,
            trading_address_town='',
            uk_region_id=None,
            archived=True,
            archived_reason='Dissolved',
        )
        url = reverse('api-v3:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']

    def test_unarchive_company(self):
        """Unarchive a company."""
        company = CompanyFactory(
            archived=True, archived_on=now(), archived_reason='foo'
        )
        url = reverse('api-v3:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(company.id)


class TestAuditLogView(APITestMixin):
    """Tests for the audit log view."""

    def test_audit_log_view(self):
        """Test retrieval of audit log."""
        initial_datetime = now()
        with reversion.create_revision():
            company = CompanyFactory(
                description='Initial desc',
            )

            reversion.set_comment('Initial')
            reversion.set_date_created(initial_datetime)
            reversion.set_user(self.user)

        changed_datetime = now()
        with reversion.create_revision():
            company.description = 'New desc'
            company.save()

            reversion.set_comment('Changed')
            reversion.set_date_created(changed_datetime)
            reversion.set_user(self.user)

        versions = Version.objects.get_for_object(company)
        version_id = versions[0].id
        url = reverse('api-v3:company:audit-item', kwargs={'pk': company.pk})

        response = self.api_client.get(url)
        response_data = response.json()['results']

        # No need to test the whole response
        assert len(response_data) == 1
        entry = response_data[0]

        assert entry['id'] == version_id
        assert entry['user']['name'] == self.user.name
        assert entry['comment'] == 'Changed'
        assert entry['timestamp'] == format_date_or_datetime(changed_datetime)
        assert entry['changes']['description'] == ['Initial desc', 'New desc']
        assert not {'created_on', 'created_by', 'modified_on', 'modified_by'} & entry[
            'changes'].keys()


class TestCHCompany(APITestMixin):
    """CH company tests."""

    def test_list_ch_companies(self):
        """List the companies house companies."""
        CompaniesHouseCompanyFactory()
        CompaniesHouseCompanyFactory()

        url = reverse('api-v3:ch-company:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == CompaniesHouseCompany.objects.all().count()

    def test_get_ch_company(self):
        """Test retrieving a single CH company."""
        ch_company = CompaniesHouseCompanyFactory()
        url = reverse(
            'api-v3:ch-company:item', kwargs={'company_number': ch_company.company_number}
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['company_number'] == ch_company.company_number

    def test_get_ch_company_alphanumeric(self):
        """Test retrieving a single CH company where the company number contains letters."""
        CompaniesHouseCompanyFactory(company_number='SC00001234')
        url = reverse(
            'api-v3:ch-company:item', kwargs={'company_number': 'SC00001234'}
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['company_number'] == 'SC00001234'

    def test_ch_company_cannot_be_written(self):
        """Test CH company POST is not allowed."""
        url = reverse('api-v3:ch-company:collection')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
