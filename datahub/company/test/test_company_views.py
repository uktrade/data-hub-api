from datetime import datetime

import factory
import pytest
import reversion
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import CompaniesHouseCompany, Company
from datahub.company.test.factories import (
    AdviserFactory,
    CompaniesHouseCompanyFactory,
    CompanyCoreTeamMemberFactory,
    CompanyFactory,
)
from datahub.core.constants import Country, HeadquarterType, Sector, UKRegion
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin, create_test_user, format_date_or_datetime, random_obj_for_model,
)
from datahub.metadata.models import CompanyClassification
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

    def test_filter_by_global_headquarters(self):
        """Test filtering by global_headquarters_id."""
        ghq = CompanyFactory()
        subsidiaries = CompanyFactory.create_batch(2, global_headquarters=ghq)
        CompanyFactory.create_batch(2)

        url = reverse('api-v3:company:collection')
        response = self.api_client.get(
            url,
            data={
                'global_headquarters_id': ghq.pk,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(subsidiaries)
        expected_ids = {str(subsidiary.pk) for subsidiary in subsidiaries}
        actual_ids = {result['id'] for result in response_data['results']}
        assert expected_ids == actual_ids

    def test_sort_by_name(self):
        """Test sorting by name."""
        companies = CompanyFactory.create_batch(
            5,
            name=factory.Iterator(
                (
                    'Mercury Ltd',
                    'Venus Ltd',
                    'Mars Components Ltd',
                    'Exports Ltd',
                    'Lambda Plc',
                ),
            ),
        )

        url = reverse('api-v3:company:collection')
        response = self.api_client.get(
            url,
            data={'sortby': 'name'},
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(companies)

        actual_names = [result['name'] for result in response_data['results']]
        assert actual_names == [
            'Exports Ltd',
            'Lambda Plc',
            'Mars Components Ltd',
            'Mercury Ltd',
            'Venus Ltd',
        ]

    def test_sort_by_created_on(self):
        """Test sorting by created_on."""
        creation_times = [
            datetime(2015, 1, 1),
            datetime(2016, 1, 1),
            datetime(2019, 1, 1),
            datetime(2020, 1, 1),
            datetime(2005, 1, 1),
        ]
        for creation_time in creation_times:
            with freeze_time(creation_time):
                CompanyFactory()

        url = reverse('api-v3:company:collection')
        response = self.api_client.get(
            url,
            data={
                'sortby': 'created_on',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(creation_times)
        expected_timestamps = [
            format_date_or_datetime(creation_time)
            for creation_time in sorted(creation_times)
        ]
        actual_timestamps = [result['created_on'] for result in response_data['results']]
        assert expected_timestamps == actual_timestamps

    def test_list_companies_without_view_document_permission(self):
        """List the companies by user without view document permission."""
        CompanyFactory.create_batch(5, archived_documents_url_path='hello world')

        user = create_test_user(
            permission_codenames=(
                'view_company',
            ),
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

    def test_list_companies_with_view_document_permission(self):
        """List the companies by user with view document permission."""
        CompanyFactory.create_batch(5, archived_documents_url_path='hello world')

        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_company_document',
            ),
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

    def test_get_company_without_view_document_permission(self):
        """Tests the company item view without view document permission."""
        company = CompanyFactory(
            archived_documents_url_path='http://some-documents',
        )
        user = create_test_user(
            permission_codenames=(
                'view_company',
            ),
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
            registered_address_country_id=Country.united_states.value.id,
        )
        company = CompanyFactory(
            company_number=123,
            name='Bar Ltd',
            alias='Xyz trading',
            vat_number='009485769',
            registered_address_1='Goodbye St',
            registered_address_town='Barland',
            registered_address_country_id=Country.united_kingdom.value.id,
            one_list_account_owner=AdviserFactory(),
        )
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_company_document',
            ),
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
                'company_category': ch_company.company_category,
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
            'archived': False,
            'archived_by': None,
            'archived_documents_url_path': company.archived_documents_url_path,
            'archived_on': None,
            'archived_reason': None,
            'business_type': {
                'id': str(company.business_type.id),
                'name': company.business_type.name,
            },
            'classification': None,
            'company_number': '123',
            'contacts': [],
            'created_on': format_date_or_datetime(company.created_on),
            'description': None,
            'employee_range': {
                'id': str(company.employee_range.id),
                'name': company.employee_range.name,
            },
            'export_experience_category': {
                'id': str(company.export_experience_category.id),
                'name': company.export_experience_category.name,
            },
            'export_to_countries': [],
            'future_interest_countries': [],
            'headquarter_type': None,
            'modified_on': format_date_or_datetime(company.modified_on),
            'one_list_account_owner': {
                'id': str(company.one_list_account_owner.pk),
                'name': company.one_list_account_owner.name,
                'first_name': company.one_list_account_owner.first_name,
                'last_name': company.one_list_account_owner.last_name,
                'dit_team': {
                    'id': str(company.one_list_account_owner.dit_team.id),
                    'name': company.one_list_account_owner.dit_team.name,
                },
            },
            'global_headquarters': None,
            'sector': {
                'id': str(company.sector.id),
                'name': company.sector.name,
            },
            'trading_address_1': company.trading_address_1,
            'trading_address_2': None,
            'trading_address_country': {
                'id': str(company.trading_address_country.id),
                'name': company.trading_address_country.name,
            },
            'trading_address_county': None,
            'trading_address_postcode': None,
            'trading_address_town': 'Woodside',
            'turnover_range': {
                'id': str(company.turnover_range.id),
                'name': company.turnover_range.name,
            },
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
            classification=random_obj_for_model(CompanyClassification),
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
            'id': str(company.registered_address_country.pk),
        }
        assert response.data['registered_address_county'] is None
        assert response.data['registered_address_postcode'] is None
        assert (response.data['headquarter_type']['id'] ==
                HeadquarterType.ukhq.value.id)
        assert response.data['classification'] == {
            'id': str(company.classification.pk),
            'name': company.classification.name,
        }

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
            classification=random_obj_for_model(CompanyClassification),
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
        assert response.data['uk_based'] is None

    @pytest.mark.parametrize(
        'input_website,expected_website',
        (
            ('www.google.com', 'http://www.google.com'),
            ('http://www.google.com', 'http://www.google.com'),
            ('https://www.google.com', 'https://www.google.com'),
            ('', ''),
            (None, None),
        ),
    )
    def test_get_company_with_website(self, input_website, expected_website):
        """
        Test that if the website field on a company doesn't have any scheme
        specified, the endpoint adds it automatically.
        """
        company = CompanyFactory(
            website=input_website,
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
            registered_address_country_id=Country.united_states.value.id,
        )

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'name': 'Acme',
            },
        )

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
            registered_address_country_id=Country.united_states.value.id,
        )
        company = CompanyFactory(
            company_number=123,
            name='Bar Ltd',
            alias='Xyz trading',
            vat_number='009485769',
            registered_address_1='Goodbye St',
            registered_address_town='Barland',
            registered_address_country_id=Country.united_kingdom.value.id,
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})

        update_data = {
            'name': 'New name',
            'registered_address_1': 'New address 1',
            'registered_address_town': 'New town',
            'registered_address_country': Country.united_states.value.id,
        }

        response = self.api_client.patch(url, data=update_data)

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
        response = self.api_client.patch(
            url,
            data={
                'reference_code': 'XYZ',
                'archived_documents_url_path': 'new_path',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['reference_code'] == 'ORG-345645'
        assert response.data['archived_documents_url_path'] == 'old_path'

    def test_long_trading_name(self):
        """Test that providing a long trading name doesn't return a 500."""
        company = CompanyFactory(
            name='Foo ltd.',
            registered_address_1='Hello st.',
            registered_address_town='Fooland',
            registered_address_country_id=Country.united_states.value.id,
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'trading_name': 'a' * 600,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'trading_name': ['Ensure this field has no more than 255 characters.'],
        }

    @pytest.mark.parametrize(
        'field,value',
        (
            ('sector', Sector.aerospace_assembly_aircraft.value.id),
        ),
    )
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
            f'{field}_id': value,
        }
        company = CompanyFactory(**creation_data)

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                field: None,
            },
        )

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
            f'{field}_id': None,
        }
        company = CompanyFactory(**creation_data)

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                field: None,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[field] is None

    @pytest.mark.parametrize(
        'hq,is_valid',
        (
            (HeadquarterType.ehq.value.id, False),
            (HeadquarterType.ukhq.value.id, False),
            (HeadquarterType.ghq.value.id, True),
            (None, False),
        ),
    )
    def test_update_company_global_headquarters_with_not_a_global_headquarters(self, hq, is_valid):
        """Tests if adding company that is not a Global HQ as a Global HQ
        will fail or if added company is a Global HQ then it will pass.
        """
        company = CompanyFactory()
        headquarter = CompanyFactory(headquarter_type_id=hq)

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'global_headquarters': headquarter.id,
            },
        )
        if is_valid:
            assert response.status_code == status.HTTP_200_OK
            if hq is not None:
                assert response.data['global_headquarters']['id'] == str(headquarter.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error = ['Company to be linked as global headquarters must be a global headquarters.']
            assert response.data['global_headquarters'] == error

    def test_remove_global_headquarters_link(self):
        """Tests that we can remove global headquarter link."""
        global_headquarters = CompanyFactory(
            headquarter_type_id=HeadquarterType.ghq.value.id,
        )
        company = CompanyFactory(global_headquarters=global_headquarters)

        assert global_headquarters.subsidiaries.count() == 1

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'global_headquarters': None,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['global_headquarters'] is None

        assert global_headquarters.subsidiaries.count() == 0

    def test_cannot_point_company_to_itself_as_global_headquarters(self):
        """Test that you cannot point company as its own global headquarters."""
        company = CompanyFactory(
            headquarter_type_id=HeadquarterType.ghq.value.id,
        )

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'global_headquarters': company.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = ['Global headquarters cannot point to itself.']
        assert response.data['global_headquarters'] == error

    def test_subsidiary_cannot_become_a_global_headquarters(self):
        """Tests that subsidiary cannot become a global headquarter."""
        global_headquarters = CompanyFactory(
            headquarter_type_id=HeadquarterType.ghq.value.id,
        )
        company = CompanyFactory(
            headquarter_type_id=None,
            global_headquarters=global_headquarters,
        )

        assert global_headquarters.subsidiaries.count() == 1

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'headquarter_type': HeadquarterType.ghq.value.id,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = ['A company cannot both be and have a global headquarters.']
        assert response.data['headquarter_type'] == error

    @pytest.mark.parametrize(
        'headquarter_type_id,changed_to,has_subsidiaries,is_valid',
        (
            (HeadquarterType.ghq.value.id, None, True, False),
            (HeadquarterType.ghq.value.id, HeadquarterType.ehq.value.id, True, False),
            (HeadquarterType.ghq.value.id, HeadquarterType.ehq.value.id, False, True),
            (HeadquarterType.ghq.value.id, None, False, True),
        ),
    )
    def test_update_headquarter_type(
        self,
        headquarter_type_id,
        changed_to,
        has_subsidiaries,
        is_valid,
    ):
        """Test updating headquarter type."""
        company = CompanyFactory(
            headquarter_type_id=headquarter_type_id,
        )
        if has_subsidiaries:
            CompanyFactory(global_headquarters=company)
            assert company.subsidiaries.count() == 1

        # now update it
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'headquarter_type': changed_to,
            },
        )

        if is_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response.data['id'] == str(company.id)
            company.refresh_from_db()
            assert str(company.headquarter_type_id) == str(changed_to)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error = ['Subsidiaries have to be unlinked before changing headquarter type.']
            assert response.data['headquarter_type'] == error


class TestAddCompany(APITestMixin):
    """Tests for adding a company."""

    def test_add_uk_company(self):
        """Test add new UK company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'
        assert response.data['trading_name'] == 'Trading name'

    def test_promote_a_ch_company(self):
        """Promote a CH company to full company."""
        CompaniesHouseCompanyFactory(company_number=1234567890)

        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
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
                'uk_region': UKRegion.england.value.id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_uk_company_without_uk_region(self):
        """Test add new UK without UK region company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': None,
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {'uk_region': ['This field is required.']}

    def test_add_not_uk_company(self):
        """Test add new not UK company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': None,
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_states.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'

    def test_add_company_partial_trading_address(self):
        """Test add new company with partial trading address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'trading_address_1': 'test',
                'uk_region': {'id': UKRegion.england.value.id},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'trading_address_town': ['This field is required.'],
            'trading_address_country': ['This field is required.'],
        }

    def test_add_company_with_trading_address(self):
        """Test add new company with trading_address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'trading_address_country': {'id': Country.ireland.value.id},
                'trading_address_1': '1 Hello st.',
                'trading_address_town': 'Dublin',
                'uk_region': {'id': UKRegion.england.value.id},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_company_without_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': None,
                'business_type': BusinessTypeConstant.company.value.id,
                'sector': Sector.aerospace_assembly_aircraft.value.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field is required.'],
            'registered_address_town': ['This field is required.'],
            'registered_address_country': ['This field is required.'],
        }

    def test_add_company_with_null_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': None,
                'business_type': BusinessTypeConstant.company.value.id,
                'sector': Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_1': None,
                'registered_address_town': None,
                'registered_address_country': None,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field may not be null.'],
            'registered_address_town': ['This field may not be null.'],
            'registered_address_country': ['This field may not be null.'],
        }

    def test_add_company_with_blank_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': None,
                'business_type': BusinessTypeConstant.company.value.id,
                'sector': Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_1': '',
                'registered_address_town': '',
                'registered_address_country': None,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'registered_address_1': ['This field may not be blank.'],
            'registered_address_town': ['This field may not be blank.'],
            'registered_address_country': ['This field may not be null.'],
        }

    @pytest.mark.parametrize('field', ('sector',))
    def test_add_company_without_required_field(self, field):
        """
        Tests adding a company without required fields that are allowed to be null (during
        updates) when already null.
        """
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'alias': None,
                'business_type': BusinessTypeConstant.company.value.id,
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'registered_address_country': Country.united_kingdom.value.id,
                'uk_region': UKRegion.england.value.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[field] == ['This field is required.']

    @pytest.mark.parametrize(
        'input_website,expected_website',
        (
            ('www.google.com', 'http://www.google.com'),
            ('http://www.google.com', 'http://www.google.com'),
            ('https://www.google.com', 'https://www.google.com'),
            ('', ''),
            (None, None),
        ),
    )
    def test_add_company_with_website(self, input_website, expected_website):
        """Test add new company with trading_address."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'trading_address_country': {'id': Country.ireland.value.id},
                'trading_address_1': '1 Hello st.',
                'trading_address_town': 'Dublin',
                'uk_region': {'id': UKRegion.england.value.id},
                'website': input_website,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['website'] == expected_website

    def test_add_uk_establishment(self):
        """Test adding a UK establishment."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                'company_number': 'BR000006',
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['company_number'] == 'BR000006'

    def test_cannot_add_uk_establishment_without_number(self):
        """Test that a UK establishment cannot be added without a company number."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                'company_number': '',
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company_number': ['This field is required.'],
        }

    def test_cannot_add_uk_establishment_as_foreign_company(self):
        """Test that adding a UK establishment fails if its country is not UK."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                'company_number': 'BR000006',
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_states.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'registered_address_country':
                ['A UK establishment (branch of non-UK company) must be in the UK.'],
        }

    def test_cannot_add_uk_establishment_invalid_prefix(self):
        """
        Test that adding a UK establishment fails if its company number does not start with BR.
        """
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                'company_number': 'SC000006',
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company_number':
                ['This must be a valid UK establishment number, beginning with BR.'],
        }

    def test_cannot_add_uk_establishment_invalid_characters(self):
        """
        Test that adding a UK establishment fails if its company number contains invalid
        characters.
        """
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                'company_number': 'BR000444é',
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company_number':
                [
                    'This field can only contain the letters A to Z and numbers (no symbols, '
                    'punctuation or spaces).',
                ],
        }

    def test_no_company_number_validation_for_normal_uk_companies(self):
        """Test that no validation is done on company number for normal companies."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(
            url,
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.private_limited_company.value.id},
                'company_number': 'sc000444é',
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
                'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                'classification': {'id': random_obj_for_model(CompanyClassification).pk},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['company_number'] == 'sc000444é'


class TestArchiveCompany(APITestMixin):
    """Archive company tests."""

    def test_archive_company_no_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'reason': ['This field is required.'],
        }

    def test_archive_company_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, data={'reason': 'foo'})

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
        response = self.api_client.post(url, data={'reason': 'foo'})

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
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']

    def test_unarchive_company(self):
        """Unarchive a company."""
        company = CompanyFactory(
            archived=True, archived_on=now(), archived_reason='foo',
        )
        url = reverse('api-v3:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']
        assert response.data['archived_reason'] == ''
        assert response.data['id'] == str(company.id)


class TestCompanyVersioning(APITestMixin):
    """
    Tests for versions created when interacting with the company endpoints.
    """

    def test_add_creates_a_new_version(self):
        """Test that creating a company creates a new version."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse('api-v3:company:collection'),
            data={
                'name': 'Acme',
                'trading_name': 'Trading name',
                'business_type': {'id': BusinessTypeConstant.company.value.id},
                'sector': {'id': Sector.aerospace_assembly_aircraft.value.id},
                'registered_address_country': {
                    'id': Country.united_kingdom.value.id,
                },
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': {'id': UKRegion.england.value.id},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Acme'
        assert response.data['trading_name'] == 'Trading name'

        company = Company.objects.get(pk=response.data['id'])

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert version.field_dict['name'] == 'Acme'
        assert version.field_dict['alias'] == 'Trading name'
        assert not any(set(version.field_dict) & set(EXCLUDED_BASE_MODEL_FIELDS))

    def test_promoting_a_ch_company_creates_a_new_version(self):
        """Test that promoting a CH company to full company creates a new version."""
        assert Version.objects.count() == 0
        CompaniesHouseCompanyFactory(company_number=1234567890)

        response = self.api_client.post(
            reverse('api-v3:company:collection'),
            data={
                'name': 'Acme',
                'company_number': 1234567890,
                'business_type': BusinessTypeConstant.company.value.id,
                'sector': Sector.aerospace_assembly_aircraft.value.id,
                'registered_address_country': Country.united_kingdom.value.id,
                'registered_address_1': '75 Stramford Road',
                'registered_address_town': 'London',
                'uk_region': UKRegion.england.value.id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        company = Company.objects.get(pk=response.data['id'])

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.field_dict['company_number'] == '1234567890'

    def test_add_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse('api-v3:company:collection'),
            data={'name': 'Acme'},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.count() == 0

    def test_update_creates_a_new_version(self):
        """Test that updating a company creates a new version."""
        company = CompanyFactory(name='Foo ltd.')

        assert Version.objects.get_for_object(company).count() == 0

        response = self.api_client.patch(
            reverse('api-v3:company:item', kwargs={'pk': company.pk}),
            data={'name': 'Acme'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Acme'

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert version.field_dict['name'] == 'Acme'

    def test_update_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        company = CompanyFactory()

        response = self.api_client.patch(
            reverse('api-v3:company:item', kwargs={'pk': company.pk}),
            data={'trading_name': 'a' * 600},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(company).count() == 0

    def test_archive_creates_a_new_version(self):
        """Test that archiving a company creates a new version."""
        company = CompanyFactory()
        assert Version.objects.get_for_object(company).count() == 0

        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, data={'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived']
        assert response.data['archived_reason'] == 'foo'

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert version.field_dict['archived']
        assert version.field_dict['archived_reason'] == 'foo'

    def test_archive_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        company = CompanyFactory()
        assert Version.objects.get_for_object(company).count() == 0

        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(company).count() == 0

    def test_unarchive_creates_a_new_version(self):
        """Test that unarchiving a company creates a new version."""
        company = CompanyFactory(
            archived=True, archived_on=now(), archived_reason='foo',
        )
        assert Version.objects.get_for_object(company).count() == 0

        url = reverse('api-v3:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert not response.data['archived']
        assert response.data['archived_reason'] == ''

        # check version created
        assert Version.objects.get_for_object(company).count() == 1
        version = Version.objects.get_for_object(company).first()
        assert version.revision.user == self.user
        assert not version.field_dict['archived']


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
        assert not set(EXCLUDED_BASE_MODEL_FIELDS) & entry['changes'].keys()


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
            'api-v3:ch-company:item', kwargs={'company_number': ch_company.company_number},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': ch_company.id,
            'business_type': {
                'id': str(ch_company.business_type.id),
                'name': ch_company.business_type.name,
            },
            'company_number': ch_company.company_number,
            'company_category': ch_company.company_category,
            'company_status': ch_company.company_status,
            'incorporation_date': format_date_or_datetime(ch_company.incorporation_date),
            'name': ch_company.name,
            'registered_address_1': ch_company.registered_address_1,
            'registered_address_2': ch_company.registered_address_2,
            'registered_address_town': ch_company.registered_address_town,
            'registered_address_county': ch_company.registered_address_county,
            'registered_address_postcode': ch_company.registered_address_postcode,
            'registered_address_country': {
                'id': str(ch_company.registered_address_country.id),
                'name': ch_company.registered_address_country.name,
            },
            'sic_code_1': ch_company.sic_code_1,
            'sic_code_2': ch_company.sic_code_2,
            'sic_code_3': ch_company.sic_code_3,
            'sic_code_4': ch_company.sic_code_4,
            'uri': ch_company.uri,
        }

    def test_get_ch_company_alphanumeric(self):
        """Test retrieving a single CH company where the company number contains letters."""
        CompaniesHouseCompanyFactory(company_number='SC00001234')
        url = reverse(
            'api-v3:ch-company:item', kwargs={'company_number': 'SC00001234'},
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


class TestCompanyCoreTeam(APITestMixin):
    """Tests for getting the core team of a company."""

    def test_empty_list(self):
        """
        Test that if company.one_list_account_owner is null and no CompanyCoreTeamMember
        records for that company exist, the endpoint returns an empty list.
        """
        company = CompanyFactory(one_list_account_owner=None)

        url = reverse(
            'api-v3:company:core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_with_only_global_account_manager(self):
        """
        Test that if company.one_list_account_owner is not null and no CompanyCoreTeamMember
        records for that company exist, the endpoint returns a list with only that adviser in it.
        """
        global_account_manager = AdviserFactory()
        company = CompanyFactory(one_list_account_owner=global_account_manager)

        url = reverse(
            'api-v3:company:core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(global_account_manager.pk),
                    'name': global_account_manager.name,
                    'first_name': global_account_manager.first_name,
                    'last_name': global_account_manager.last_name,
                    'dit_team': {
                        'id': str(global_account_manager.dit_team.pk),
                        'name': global_account_manager.dit_team.name,
                        'uk_region': {
                            'id': str(global_account_manager.dit_team.uk_region.pk),
                            'name': global_account_manager.dit_team.uk_region.name,
                        },
                        'country': {
                            'id': str(global_account_manager.dit_team.country.pk),
                            'name': global_account_manager.dit_team.country.name,
                        },
                    },
                },
                'is_global_account_manager': True,
            },
        ]

    @pytest.mark.parametrize(
        'with_global_account_manager',
        (True, False),
        ids=lambda val: f'{"With" if val else "Without"} global account manager',
    )
    def test_with_core_team_members(self, with_global_account_manager):
        """
        Test that if CompanyCoreTeamMember records for this company exist, the endpoint
        returns a list with all team members in it.
        company.one_list_account_owner (the global account manager) is included and counted
        only once if set.
        """
        team_member_advisers = AdviserFactory.create_batch(
            3,
            first_name=factory.Iterator(
                ('Adam', 'Barbara', 'Chris'),
            ),
        )
        global_account_manager = team_member_advisers[0] if with_global_account_manager else None

        company = CompanyFactory(one_list_account_owner=global_account_manager)
        CompanyCoreTeamMemberFactory.create_batch(
            len(team_member_advisers),
            company=company,
            adviser=factory.Iterator(team_member_advisers),
        )

        url = reverse(
            'api-v3:company:core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                'adviser': {
                    'id': str(adviser.pk),
                    'name': adviser.name,
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                    'dit_team': {
                        'id': str(adviser.dit_team.pk),
                        'name': adviser.dit_team.name,
                        'uk_region': {
                            'id': str(adviser.dit_team.uk_region.pk),
                            'name': adviser.dit_team.uk_region.name,
                        },
                        'country': {
                            'id': str(adviser.dit_team.country.pk),
                            'name': adviser.dit_team.country.name,
                        },
                    },
                },
                'is_global_account_manager': adviser is global_account_manager,
            }
            for adviser in team_member_advisers
        ]

    def test_404_with_invalid_company(self):
        """
        Test that if the company doesn't exist, the endpoint returns 404.
        """
        url = reverse(
            'api-v3:company:core-team',
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
