import uuid
from datetime import datetime

import factory
import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import (
    Company,
    OneListTier,
)
from datahub.company.serializers import CompanySerializer
from datahub.company.test.factories import (
    AdviserFactory,
    CompanyExportCountryFactory,
    CompanyFactory,
)
from datahub.company.test.utils import address_area_or_none
from datahub.core.constants import Country, EmployeeRange, HeadquarterType, TurnoverRange, UKRegion
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
    random_obj_for_model,
)
from datahub.metadata.models import Sector
from datahub.metadata.test.factories import TeamFactory


class TestListCompanies(APITestMixin):
    """Tests for listing companies."""

    def test_companies_list_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v4:company:collection')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_companies(self):
        """List the companies."""
        CompanyFactory.create_batch(2)
        url = reverse('api-v4:company:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['count'] == 2

    def test_filter_by_global_headquarters(self):
        """Test filtering by global_headquarters_id."""
        ghq = CompanyFactory()
        subsidiaries = CompanyFactory.create_batch(2, global_headquarters=ghq)
        CompanyFactory.create_batch(2)

        url = reverse('api-v4:company:collection')
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

    def test_filter_by_global_ultimate_duns_number(self):
        """Test filtering by global_ultimate_duns_number."""
        ultimate_duns = '123456789'
        ultimate_company = CompanyFactory(
            duns_number=ultimate_duns,
            global_ultimate_duns_number=ultimate_duns,
        )
        subsidiaries = CompanyFactory.create_batch(2, global_ultimate_duns_number=ultimate_duns)
        all_companies = [ultimate_company] + subsidiaries
        CompanyFactory.create_batch(2)

        url = reverse('api-v4:company:collection')
        response = self.api_client.get(
            url,
            data={
                'global_ultimate_duns_number': ultimate_duns,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(all_companies)
        expected_ids = {str(company.pk) for company in all_companies}
        for result_company in response_data['results']:
            assert result_company['id'] in expected_ids
            # Ensure that global ultimates are marked correctly
            if result_company['is_global_ultimate']:
                assert result_company['id'] == str(ultimate_company.id)

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

        url = reverse('api-v4:company:collection')
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

        url = reverse('api-v4:company:collection')
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
        url = reverse('api-v4:company:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5
        assert all(
            'archived_documents_url_path' not in company
            for company in response_data['results']
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
        url = reverse('api-v4:company:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 5
        assert all(
            company['archived_documents_url_path'] == 'hello world'
            for company in response_data['results']
        )


class TestGetCompany(APITestMixin):
    """Tests for getting a company."""

    def test_get_company_without_view_document_permission(self):
        """
        Tests that if the user doesn't have view document permission,
        the response body will not include archived_documents_url_path.
        """
        company = CompanyFactory(
            archived_documents_url_path='http://some-documents',
        )
        user = create_test_user(
            permission_codenames=(
                'view_company',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'archived_documents_url_path' not in response.json()

    def test_get(self):
        """Tests the company item view."""
        ghq = CompanyFactory(
            global_headquarters=None,
            one_list_tier=OneListTier.objects.first(),
            one_list_account_owner=AdviserFactory(),
        )
        company = CompanyFactory(
            company_number='123',
            trading_names=['Xyz trading', 'Abc trading'],
            global_headquarters=ghq,
            one_list_tier=None,
            one_list_account_owner=None,
            export_to_countries=[],
            future_interest_countries=[],
        )
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_company_document',
                'view_companyexportcountry',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(company.pk),
            'created_on': format_date_or_datetime(company.created_on),
            'modified_on': format_date_or_datetime(company.modified_on),
            'name': company.name,
            'reference_code': company.reference_code,
            'company_number': company.company_number,
            'vat_number': company.vat_number,
            'duns_number': company.duns_number,
            'trading_names': company.trading_names,
            'address': {
                'line_1': company.address_1,
                'line_2': company.address_2 or '',
                'town': company.address_town,
                'county': company.address_county or '',
                'postcode': company.address_postcode or '',
                'area': address_area_or_none(company.address_area),
                'country': {
                    'id': str(company.address_country.id),
                    'name': company.address_country.name,
                },
            },
            'registered_address': {
                'line_1': company.registered_address_1,
                'line_2': company.registered_address_2 or '',
                'town': company.registered_address_town,
                'county': company.registered_address_county or '',
                'postcode': company.registered_address_postcode or '',
                'area': address_area_or_none(company.registered_address_area),
                'country': {
                    'id': str(company.registered_address_country.id),
                    'name': company.registered_address_country.name,
                },
            },
            'uk_based': (
                company.address_country.id == uuid.UUID(Country.united_kingdom.value.id)
            ),
            'uk_region': {
                'id': str(company.uk_region.id),
                'name': company.uk_region.name,
            },
            'business_type': {
                'id': str(company.business_type.id),
                'name': company.business_type.name,
            },
            'contacts': [],
            'description': company.description,
            'employee_range': {
                'id': str(company.employee_range.id),
                'name': company.employee_range.name,
            },
            'number_of_employees': company.number_of_employees,
            'is_number_of_employees_estimated': company.is_number_of_employees_estimated,
            'export_experience_category': {
                'id': str(company.export_experience_category.id),
                'name': company.export_experience_category.name,
            },
            'export_potential': None,
            'great_profile_status': None,
            'export_to_countries': [],
            'future_interest_countries': [],
            'headquarter_type': company.headquarter_type,
            'sector': {
                'id': str(company.sector.id),
                'name': company.sector.name,
            },
            'export_segment': company.export_segment,
            'export_sub_segment': company.export_sub_segment,
            'turnover_range': {
                'id': str(company.turnover_range.id),
                'name': company.turnover_range.name,
            },
            'turnover': company.turnover,
            'is_turnover_estimated': company.is_turnover_estimated,
            'website': company.website,
            'global_headquarters': {
                'id': str(ghq.id),
                'name': ghq.name,
            },
            'one_list_group_tier': {
                'id': str(ghq.one_list_tier.id),
                'name': ghq.one_list_tier.name,
            },
            'one_list_group_global_account_manager': {
                'id': str(ghq.one_list_account_owner.pk),
                'name': ghq.one_list_account_owner.name,
                'first_name': ghq.one_list_account_owner.first_name,
                'last_name': ghq.one_list_account_owner.last_name,
                'contact_email': ghq.one_list_account_owner.contact_email,
                'dit_team': {
                    'id': str(ghq.one_list_account_owner.dit_team.id),
                    'name': ghq.one_list_account_owner.dit_team.name,
                    'uk_region': {
                        'id': str(ghq.one_list_account_owner.dit_team.uk_region.pk),
                        'name': ghq.one_list_account_owner.dit_team.uk_region.name,
                    },
                    'country': {
                        'id': str(ghq.one_list_account_owner.dit_team.country.pk),
                        'name': ghq.one_list_account_owner.dit_team.country.name,
                    },
                },
            },
            'export_countries': [],
            'archived_documents_url_path': company.archived_documents_url_path,
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
            'transferred_by': None,
            'transferred_on': None,
            'transferred_to': None,
            'transfer_reason': '',
            'pending_dnb_investigation': False,
            'is_global_ultimate': company.is_global_ultimate,
            'global_ultimate_duns_number': company.global_ultimate_duns_number,
            'dnb_modified_on': company.dnb_modified_on,
        }

    def test_get_company_without_country(self):
        """
        Tests the company item view for a company without a country.

        Checks that the endpoint returns 200 and the uk_based attribute is
        set to None.
        """
        company = CompanyFactory(
            address_country_id=None,
        )

        url = reverse('api-v4:company:item', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['uk_based'] is None

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
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['website'] == expected_website

    @pytest.mark.parametrize(
        'pending_dnb_investigation',
        (
            True,
            False,
        ),
    )
    def test_get_company_pending_dnb_investigation(self, pending_dnb_investigation):
        """
        Test that `pending_dnb_investigation` is set for a company API result
        as expected.
        """
        company = CompanyFactory(
            pending_dnb_investigation=pending_dnb_investigation,
        )
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['pending_dnb_investigation'] == pending_dnb_investigation

    @pytest.mark.parametrize(
        'is_global_ultimate',
        (
            True,
            False,
        ),
    )
    def test_get_company_is_global_ultimate(self, is_global_ultimate):
        """
        Test that `is_global_ultimate` is set for a company API result
        as expected.
        """
        kwargs = {}
        if is_global_ultimate:
            kwargs['duns_number'] = 123456789
            kwargs['global_ultimate_duns_number'] = 123456789
        company = CompanyFactory(**kwargs)
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_global_ultimate'] == is_global_ultimate

    @pytest.mark.parametrize(
        'global_ultimate_overrides',
        (
            {'global_ultimate_duns_number': ''},
            {'global_ultimate_duns_number': '123456789'},
            {'global_ultimate_duns_number': '123456789', 'duns_number': '123456789'},
        ),
    )
    def test_get_company_global_ultimate_duns_number(self, global_ultimate_overrides):
        """
        Test that `global_ultimate_duns_number` is set for a company API result
        as expected.
        """
        company = CompanyFactory(
            **global_ultimate_overrides,
        )
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        global_ultimate_duns_number = global_ultimate_overrides['global_ultimate_duns_number']
        assert response.json()['global_ultimate_duns_number'] == global_ultimate_duns_number

    def test_get_company_with_export_countries(self):
        """
        Tests the company response has export countries that are
        in the new CompanyExportCountry model.
        """
        company = CompanyFactory()
        export_country_one, export_country_two = CompanyExportCountryFactory.create_batch(2)
        company.export_countries.set([export_country_one, export_country_two])
        user = create_test_user(
            permission_codenames=(
                'view_company',
                'view_companyexportcountry',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json().get('export_countries', []) is not []
        export_countries_response = response.json().get('export_countries')
        assert export_countries_response == [
            {
                'country': {
                    'id': str(item.country.pk),
                    'name': item.country.name,
                },
                'status': item.status,
            } for item in company.export_countries.order_by('pk')
        ]

    def test_check_company_dont_return_export_countries_with_no_permission(self):
        """
        Tests the company response has no export countries
        without appropriate permission.
        """
        company = CompanyFactory()
        export_country_one, export_country_two = CompanyExportCountryFactory.create_batch(2)
        company.export_countries.set([export_country_one, export_country_two])
        user = create_test_user(
            permission_codenames=(
                'view_company',
            ),
        )
        api_client = self.create_api_client(user=user)

        url = reverse('api-v4:company:item', kwargs={'pk': company.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'export_countries' not in response.json()

    @pytest.mark.parametrize(
        'build_company',
        (
            # subsidiary with Global Headquarters on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(one_list_tier=one_list_tier),
            ),
            # subsidiary with Global Headquarters not on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(one_list_tier=None),
            ),
            # single company on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=one_list_tier,
                global_headquarters=None,
            ),
            # single company not on the One List
            lambda one_list_tier: CompanyFactory(
                one_list_tier=None,
                global_headquarters=None,
            ),
        ),
        ids=(
            'as_subsidiary_of_one_list_company',
            'as_subsidiary_of_non_one_list_company',
            'as_one_list_company',
            'as_non_one_list_company',
        ),
    )
    def test_one_list_group_tier(self, build_company):
        """
        Test that the endpoint includes the One List Tier
        of the Global Headquarters in the group.
        """
        one_list_tier = OneListTier.objects.first()
        company = build_company(one_list_tier)

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        group_global_headquarters = company.global_headquarters or company

        actual_one_list_group_tier = response.json()['one_list_group_tier']
        if not group_global_headquarters.one_list_tier:
            assert not actual_one_list_group_tier
        else:
            assert actual_one_list_group_tier == {
                'id': str(one_list_tier.id),
                'name': one_list_tier.name,
            }

    @pytest.mark.parametrize(
        'build_company',
        (
            # subsidiary with Global Headquarters on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(
                    one_list_tier=one_list_tier,
                    one_list_account_owner=gam,
                ),
            ),
            # subsidiary with Global Headquarters not on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=None,
                global_headquarters=CompanyFactory(
                    one_list_tier=None,
                    one_list_account_owner=None,
                ),
            ),
            # single company on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=one_list_tier,
                one_list_account_owner=gam,
                global_headquarters=None,
            ),
            # single company not on the One List
            lambda one_list_tier, gam: CompanyFactory(
                one_list_tier=None,
                global_headquarters=None,
                one_list_account_owner=None,
            ),
        ),
        ids=(
            'as_subsidiary_of_one_list_company',
            'as_subsidiary_of_non_one_list_company',
            'as_one_list_company',
            'as_non_one_list_company',
        ),
    )
    def test_one_list_group_global_account_manager(self, build_company):
        """
        Test that the endpoint includes the One List Global Account Manager
        of the Global Headquarters in the group.
        """
        global_account_manager = AdviserFactory()
        one_list_tier = OneListTier.objects.first()
        company = build_company(one_list_tier, global_account_manager)

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        group_global_headquarters = company.global_headquarters or company

        actual_global_account_manager = response.json()['one_list_group_global_account_manager']
        if not group_global_headquarters.one_list_account_owner:
            assert not actual_global_account_manager
        else:
            assert actual_global_account_manager == {
                'id': str(global_account_manager.pk),
                'name': global_account_manager.name,
                'first_name': global_account_manager.first_name,
                'last_name': global_account_manager.last_name,
                'contact_email': global_account_manager.contact_email,
                'dit_team': {
                    'id': str(global_account_manager.dit_team.id),
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
            }


class TestUpdateCompany(APITestMixin):
    """Tests for updating a single company."""

    @pytest.mark.parametrize(
        'initial_model_values,data,expected_response',
        (
            # change of names
            (
                {
                    'name': 'Some name',
                    'trading_names': ['old name'],
                },
                {
                    'name': 'Acme',
                    'trading_names': ['new name'],
                },
                {
                    'name': 'Acme',
                    'trading_names': ['new name'],
                },
            ),

            # change of address
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_area': None,
                    'address_country_id': Country.ireland.value.id,
                },
                {
                    'address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                },
                {
                    'address': {
                        'line_1': '2',
                        'line_2': 'Main Road',
                        'town': 'London',
                        'county': 'Greenwich',
                        'postcode': 'SE10 9NN',
                        'area': None,
                        'country': {
                            'id': Country.united_kingdom.value.id,
                            'name': Country.united_kingdom.value.name,
                        },
                    },
                },
            ),

            # change of registered address
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_area_id': None,
                    'address_country_id': Country.ireland.value.id,

                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_area_id': None,
                    'registered_address_country_id': Country.united_kingdom.value.id,
                },
                {
                    'registered_address': {
                        'line_1': '3',
                        'line_2': 'Secondary Road',
                        'town': 'Bristol',
                        'county': 'Bristol',
                        'postcode': 'BS5 6TX',
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                },
                {
                    'registered_address': {
                        'line_1': '3',
                        'line_2': 'Secondary Road',
                        'town': 'Bristol',
                        'county': 'Bristol',
                        'postcode': 'BS5 6TX',
                        'area': None,
                        'country': {
                            'id': Country.united_kingdom.value.id,
                            'name': Country.united_kingdom.value.name,
                        },
                    },
                },
            ),

            # set registered address to None
            (
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_area_id': None,
                    'address_country_id': Country.ireland.value.id,

                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_area_id': None,
                    'registered_address_country_id': Country.united_kingdom.value.id,
                },
                {
                    'registered_address': None,
                },
                {
                    'registered_address': None,
                },
            ),
        ),
    )
    def test_update_company(self, initial_model_values, data, expected_response):
        """Test company update."""
        company = CompanyFactory(
            **initial_model_values,
        )

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        actual_response = {
            field_name: response_data[field_name]
            for field_name in expected_response
        }
        assert actual_response == expected_response

    def test_cannot_update_read_only_fields(self):
        """Test updating read-only fields."""
        one_list_tier, different_one_list_tier = OneListTier.objects.all()[:2]
        one_list_gam, different_one_list_gam = AdviserFactory.create_batch(2)
        company = CompanyFactory(
            reference_code='ORG-345645',
            archived_documents_url_path='old_path',
            one_list_tier=one_list_tier,
            one_list_account_owner=one_list_gam,
            duns_number=None,
            turnover=100,
            is_turnover_estimated=False,
            number_of_employees=95,
            is_number_of_employees_estimated=False,
            pending_dnb_investigation=True,
            export_potential=Company.ExportPotentialScore.VERY_HIGH,
            great_profile_status=Company.GreatProfileStatus.PUBLISHED,
        )

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'reference_code': 'XYZ',
                'archived_documents_url_path': 'new_path',
                'one_list_group_tier': different_one_list_tier.id,
                'one_list_group_global_account_manager': different_one_list_gam.id,
                'duns_number': '000000002',
                'turnover': 101,
                'is_turnover_estimated': True,
                'number_of_employees': 96,
                'is_number_of_employees_estimated': True,
                'pending_dnb_investigation': False,
                'export_potential': Company.ExportPotentialScore.VERY_LOW,
                'great_profile_status': Company.GreatProfileStatus.UNPUBLISHED,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['reference_code'] == 'ORG-345645'
        assert response_data['archived_documents_url_path'] == 'old_path'
        assert response_data['one_list_group_tier'] == {
            'id': str(company.one_list_tier.id),
            'name': company.one_list_tier.name,
        }
        assert response_data['one_list_group_global_account_manager']['id'] == str(one_list_gam.id)
        assert response_data['duns_number'] is None
        assert response_data['turnover'] == 100
        assert not response_data['is_turnover_estimated']
        assert response_data['number_of_employees'] == 95
        assert not response_data['is_number_of_employees_estimated']
        assert response_data['pending_dnb_investigation']
        assert response_data['export_potential'] == Company.ExportPotentialScore.VERY_HIGH
        assert response_data['great_profile_status'] == Company.GreatProfileStatus.PUBLISHED

    def test_cannot_update_dnb_readonly_fields_if_duns_number_is_set(self):
        """
        Test that if company.duns_number is not blank, the client cannot update the
        fields defined by CompanySerializer.Meta.dnb_read_only_fields.
        """
        company = CompanyFactory(
            duns_number='012345678',
            name='name',
            trading_names=['a', 'b', 'c'],
            company_number='company number',
            vat_number='vat number',
            address_1='address 1',
            address_2='address 2',
            address_town='address town',
            address_county='address county',
            address_postcode='address postcode',
            address_country_id=Country.argentina.value.id,
            registered_address_1='registered address 1',
            registered_address_2='registered address 2',
            registered_address_town='registered address town',
            registered_address_county='registered address county',
            registered_address_postcode='registered address postcode',
            registered_address_country_id=Country.anguilla.value.id,
            website='website',
            business_type_id=BusinessTypeConstant.charity.value.id,
            employee_range_id=EmployeeRange.range_10_to_49.value.id,
            turnover_range_id=TurnoverRange.range_1_34_to_6_7.value.id,
        )

        data = {
            'name': 'new name',
            'trading_names': ['new trading name'],
            'company_number': 'new company number',
            'vat_number': 'new vat number',
            'address': {
                'line_1': 'new address 1',
                'line_2': 'new address 2',
                'town': 'new address town',
                'county': 'new address county',
                'postcode': 'new address postcode',
                'country': Country.canada.value.id,
            },
            'registered_address': {
                'line_1': 'new registered address 1',
                'line_2': 'new registered address 2',
                'town': 'new registered address town',
                'county': 'new registered address county',
                'postcode': 'new registered address postcode',
                'country': Country.azerbaijan.value.id,
            },
            'business_type': BusinessTypeConstant.community_interest_company.value.id,
            'employee_range': EmployeeRange.range_1_to_9.value.id,
            'turnover_range': TurnoverRange.range_33_5_plus.value.id,
        }

        assert set(data.keys()) == set(CompanySerializer.Meta.dnb_read_only_fields), (
            'It looks like you have changed CompanySerializer.Meta.dnb_read_only_fields, '
            'please update this test accordingly.'
        )

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        for field, value in data.items():
            assert response_data[field] != value

    @pytest.mark.parametrize(
        'data,expected_error',
        (
            # trading names too long
            (
                {'trading_names': ['a' * 600]},
                {'trading_names': {'0': ['Ensure this field has no more than 255 characters.']}},
            ),
            # sector cannot become nullable
            (
                {'sector': None},
                {'sector': ['This field is required.']},
            ),
            # uk_region is required
            (
                {'uk_region': None},
                {'uk_region': ['This field is required.']},
            ),
            # partial registered address, other fields are required
            (
                {
                    'registered_address': {
                        'line_1': 'test',
                    },
                },
                {
                    'registered_address': {
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),
            # address cannot be null
            (
                {
                    'address': None,
                },
                {
                    'address': ['This field may not be null.'],
                },
            ),
            # address cannot be null
            (
                {
                    'address': {
                        'line_1': None,
                        'town': None,
                        'country': Country.united_kingdom.value.id,
                    },
                },
                {
                    'address': {
                        'line_1': ['This field may not be null.'],
                        'town': ['This field may not be null.'],
                    },
                },
            ),
            # address cannot be empty
            (
                {
                    'address': {
                        'line_1': '',
                        'town': '',
                        'country': None,
                    },
                },
                {
                    'address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),
            # company_number required if business type == uk establishment
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': '',
                    'address': {
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                },
                {
                    'company_number': ['This field is required.'],
                },
            ),
            # country should be UK if business type == uk establishment
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': 'BR1234',
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'Cordova',
                        'country': {
                            'id': Country.united_states.value.id,
                        },
                    },
                },
                {
                    'address_country':
                        ['A UK establishment (branch of non-UK company) must be in the UK.'],
                },
            ),
        ),
    )
    def test_validation_error(self, data, expected_error):
        """Test validation scenarios."""
        company = CompanyFactory(
            registered_address_1='',
            registered_address_2='',
            registered_address_town='',
            registered_address_county='',
            registered_address_postcode='',
            registered_address_country_id=None,
        )

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    @pytest.mark.parametrize('field', ('sector',))
    def test_update_null_field_to_null(self, field):
        """
        Tests setting fields to null that are currently null, and are allowed to be null
        when already null.
        """
        company = CompanyFactory(**{f'{field}_id': None})

        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
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
        """
        Tests if adding company that is not a Global HQ as a Global HQ
        will fail or if added company is a Global HQ then it will pass.
        """
        company = CompanyFactory(
            duns_number='123456789',
        )
        headquarter = CompanyFactory(headquarter_type_id=hq)

        # now update it
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'global_headquarters': headquarter.id,
            },
        )
        response_data = response.json()
        if is_valid:
            assert response.status_code == status.HTTP_200_OK
            if hq is not None:
                assert response_data['global_headquarters']['id'] == str(headquarter.id)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error = ['Company to be linked as global headquarters must be a global headquarters.']
            assert response_data['global_headquarters'] == error

    def test_remove_global_headquarters_link(self):
        """Tests that we can remove global headquarter link."""
        global_headquarters = CompanyFactory(
            headquarter_type_id=HeadquarterType.ghq.value.id,
        )
        company = CompanyFactory(
            duns_number='123456789',
            global_headquarters=global_headquarters,
        )

        assert global_headquarters.subsidiaries.count() == 1

        # now update it
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'global_headquarters': None,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['global_headquarters'] is None

        assert global_headquarters.subsidiaries.count() == 0

    def test_cannot_point_company_to_itself_as_global_headquarters(self):
        """Test that you cannot point company as its own global headquarters."""
        company = CompanyFactory(
            headquarter_type_id=HeadquarterType.ghq.value.id,
        )

        # now update it
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'global_headquarters': company.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = ['Global headquarters cannot point to itself.']
        assert response.json()['global_headquarters'] == error

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
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'headquarter_type': HeadquarterType.ghq.value.id,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error = ['A company cannot both be and have a global headquarters.']
        assert response.json()['headquarter_type'] == error

    @pytest.mark.parametrize(
        'headquarter_type_id,changed_to,has_subsidiaries,is_valid',
        (
            (None, HeadquarterType.ghq.value.id, False, True),
            (None, HeadquarterType.ukhq.value.id, False, True),
            (None, HeadquarterType.ehq.value.id, False, True),
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
            duns_number='123456789',
            headquarter_type_id=headquarter_type_id,
        )
        if has_subsidiaries:
            CompanyFactory(global_headquarters=company)
            assert company.subsidiaries.count() == 1

        # now update it
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'headquarter_type': changed_to,
            },
        )

        response_data = response.json()
        if is_valid:
            assert response.status_code == status.HTTP_200_OK
            assert response_data['id'] == str(company.id)
            company.refresh_from_db()
            assert str(company.headquarter_type_id) == str(changed_to)
        else:
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            error = ['Subsidiaries have to be unlinked before changing headquarter type.']
            assert response_data['headquarter_type'] == error

    @pytest.mark.parametrize(
        'score',
        (
            'very_high',
            'medium',
            'low',
            None,
        ),
    )
    def test_get_company_with_export_potential(self, score):
        """
        Test imported export_potential field on a company appears as is
        """
        company = CompanyFactory(
            export_potential=score,
        )
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['export_potential'] == score

    @pytest.mark.parametrize(
        'profile_status',
        (
            Company.GreatProfileStatus.PUBLISHED,
            Company.GreatProfileStatus.UNPUBLISHED,
            None,
        ),
    )
    def test_get_company_with_great_profile_status(self, profile_status):
        """
        Test imported `great_profile_status` field on a company appears as is
        """
        company = CompanyFactory(
            great_profile_status=profile_status,
        )
        url = reverse('api-v4:company:item', kwargs={'pk': company.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['great_profile_status'] == profile_status


class TestAddCompany(APITestMixin):
    """Tests for adding a company."""

    @pytest.mark.parametrize(
        'data,expected_response',
        (
            # uk company
            (
                {
                    'name': 'Acme',
                    'trading_names': ['Trading name'],
                    'business_type': {'id': BusinessTypeConstant.company.value.id},
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'London',
                        'area': None,
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                    'uk_region': {'id': UKRegion.england.value.id},
                    'headquarter_type': {'id': HeadquarterType.ghq.value.id},
                },
                {
                    'name': 'Acme',
                    'trading_names': ['Trading name'],
                    'business_type': {
                        'id': BusinessTypeConstant.company.value.id,
                        'name': BusinessTypeConstant.company.value.name,
                    },
                    'address': {
                        'line_1': '75 Stramford Road',
                        'line_2': '',
                        'town': 'London',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': Country.united_kingdom.value.id,
                            'name': Country.united_kingdom.value.name,
                        },
                    },
                    'registered_address': None,
                    'uk_region': {
                        'id': UKRegion.england.value.id,
                        'name': UKRegion.england.value.name,
                    },
                    'headquarter_type': {
                        'id': HeadquarterType.ghq.value.id,
                        'name': HeadquarterType.ghq.value.name,
                    },
                },
            ),
            # non-UK
            (
                {
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'Cordova',
                        'area': None,
                        'country': {
                            'id': Country.united_states.value.id,
                        },
                    },
                },
                {
                    'address': {
                        'line_1': '75 Stramford Road',
                        'line_2': '',
                        'town': 'Cordova',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': Country.united_states.value.id,
                            'name': Country.united_states.value.name,
                        },
                    },
                    'registered_address': None,
                },
            ),
            # promote a CH company
            (
                {
                    'company_number': '1234567890',
                    'business_type': BusinessTypeConstant.company.value.id,
                },
                {'company_number': '1234567890'},
            ),
            # no special validation on company_number is done for non UK establishment companies
            (
                {
                    'business_type': BusinessTypeConstant.company.value.id,
                    'company_number': 'sc000444é',
                },
                {'company_number': 'sc000444é'},
            ),
            # UK establishment with correct company_number format
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': 'BR000006',
                },
                {'company_number': 'BR000006'},
            ),
            # http:// is prepended to the website if a scheme is not present
            (
                {'website': 'www.google.com'},
                {'website': 'http://www.google.com'},
            ),
            # website is not converted if it includes an http scheme
            (
                {'website': 'http://www.google.com'},
                {'website': 'http://www.google.com'},
            ),
            # website is not converted if it includes an http scheme
            (
                {'website': 'https://www.google.com'},
                {'website': 'https://www.google.com'},
            ),
            # website is not converted if it's empty
            (
                {'website': ''},
                {'website': ''},
            ),
            # website is not converted if it's None
            (
                {'website': None},
                {'website': None},
            ),
            # registered address is saved
            (
                {
                    'registered_address': {
                        'line_1': '1 Hello st.',
                        'town': 'Dublin',
                        'area': None,
                        'country': {
                            'id': Country.ireland.value.id,
                        },
                    },
                },
                {
                    'registered_address': {
                        'line_1': '1 Hello st.',
                        'line_2': '',
                        'town': 'Dublin',
                        'county': '',
                        'postcode': '',
                        'area': None,
                        'country': {
                            'id': Country.ireland.value.id,
                            'name': Country.ireland.value.name,
                        },
                    },
                },
            ),
        ),
    )
    def test_success_cases(self, data, expected_response):
        """Test success scenarios."""
        post_data = {
            'name': 'Acme',
            'business_type': BusinessTypeConstant.company.value.id,
            'sector': random_obj_for_model(Sector).id,
            'address': {
                'line_1': '75 Stramford Road',
                'town': 'London',
                'country': Country.united_kingdom.value.id,
            },
            'uk_region': UKRegion.england.value.id,

            **data,
        }

        url = reverse('api-v4:company:collection')
        response = self.api_client.post(
            url,
            data=post_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['pending_dnb_investigation']
        actual_response = {
            field_name: response_data[field_name]
            for field_name in expected_response
        }
        assert actual_response == expected_response

    def test_required_fields(self):
        """Test required fields."""
        url = reverse('api-v4:company:collection')
        response = self.api_client.post(
            url,
            data={},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'name': ['This field is required.'],
            'address': ['This field is required.'],
        }

    @pytest.mark.parametrize(
        'data,expected_error',
        (
            # uk_region is required
            (
                {'uk_region': None},
                {'uk_region': ['This field is required.']},
            ),
            # partial registered address, other fields are required
            (
                {
                    'registered_address': {
                        'line_1': 'test',
                    },
                },
                {
                    'registered_address': {
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),
            # address cannot be null
            (
                {
                    'address': None,
                },
                {
                    'address': ['This field may not be null.'],
                },
            ),
            # address cannot be null
            (
                {
                    'address': {
                        'line_1': None,
                        'town': None,
                        'country': Country.united_kingdom.value.id,
                    },
                },
                {
                    'address': {
                        'line_1': ['This field may not be null.'],
                        'town': ['This field may not be null.'],
                    },
                },
            ),
            # address cannot be empty
            (
                {
                    'address': {
                        'line_1': '',
                        'town': '',
                        'country': None,
                    },
                },
                {
                    'address': {
                        'line_1': ['This field is required.'],
                        'town': ['This field is required.'],
                        'country': ['This field is required.'],
                    },
                },
            ),
            # company_number required if business type == uk establishment
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': '',
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'London',
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                },
                {
                    'company_number': ['This field is required.'],
                },
            ),
            # country should be UK if business type == uk establishment
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': 'BR1234',
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'Cordova',
                        'country': {
                            'id': Country.united_states.value.id,
                        },
                    },
                },
                {
                    'address_country':
                        ['A UK establishment (branch of non-UK company) must be in the UK.'],
                },
            ),
            # company_number should start with BR if business type == uk establishment
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': '123',
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'London',
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                },
                {
                    'company_number':
                        ['This must be a valid UK establishment number, beginning with BR.'],
                },
            ),
            # company_number shouldn't have invalid characters
            (
                {
                    'business_type': {'id': BusinessTypeConstant.uk_establishment.value.id},
                    'company_number': 'BR000444é',
                    'address': {
                        'line_1': '75 Stramford Road',
                        'town': 'London',
                        'country': {
                            'id': Country.united_kingdom.value.id,
                        },
                    },
                },
                {
                    'company_number':
                        [
                            'This field can only contain the letters A to Z and numbers '
                            '(no symbols, punctuation or spaces).',
                        ],
                },
            ),
        ),
    )
    def test_validation_error(self, data, expected_error):
        """Test validation scenarios."""
        post_data = {
            'name': 'Acme',
            'business_type': BusinessTypeConstant.company.value.id,
            'sector': random_obj_for_model(Sector).id,
            'address': {
                'line_1': '75 Stramford Road',
                'town': 'London',
                'country': Country.united_kingdom.value.id,
            },
            'uk_region': UKRegion.england.value.id,

            **data,
        }

        url = reverse('api-v4:company:collection')
        response = self.api_client.post(
            url,
            data=post_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    def test_post_create_stub(self):
        """
        Ensure that this endpoint will provide a good drop in replacement for our V1 company
        investigation API endpoint.
        """
        payload = {
            'business_type': BusinessTypeConstant.company.value.id,
            'name': 'Test Company',
            'address': {
                'line_1': 'Foo',
                'line_2': 'Bar',
                'town': 'Baz',
                'county': 'Qux',
                'country': {
                    'id': Country.united_kingdom.value.id,
                },
                'postcode': 'AB5 XY2',
            },
            'sector': random_obj_for_model(Sector).id,
            'uk_region': UKRegion.east_midlands.value.id,
        }
        response = self.api_client.post(
            reverse('api-v4:company:collection'),
            data=payload,
        )

        assert response.status_code == status.HTTP_201_CREATED

        company = Company.objects.get(
            pk=response.json()['id'],
        )
        assert company.pending_dnb_investigation
        assert company.created_by == self.user
        assert company.modified_by == self.user
        assert company.name == payload['name']
        assert company.address_1 == payload['address']['line_1']
        assert company.address_2 == payload['address']['line_2']
        assert company.address_town == payload['address']['town']
        assert company.address_county == payload['address']['county']
        assert company.address_postcode == payload['address']['postcode']
        assert str(company.address_country.id) == payload['address']['country']['id']
        assert str(company.business_type.id) == payload['business_type']
        assert company.sector.id == payload['sector']
        assert str(company.uk_region.id) == payload['uk_region']
