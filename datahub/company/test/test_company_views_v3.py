import uuid

import factory
import pytest
import reversion
from django.forms.models import model_to_dict
from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from reversion.models import Version

from datahub.company.constants import BusinessTypeConstant
from datahub.company.models import OneListTier
from datahub.company.serializers import CompanySerializerV3
from datahub.company.test.factories import (
    AdviserFactory,
    CompaniesHouseCompanyFactory,
    CompanyFactory,
    DuplicateCompanyFactory,
    OneListCoreTeamMemberFactory,
)
from datahub.core.constants import Country, EmployeeRange, HeadquarterType, TurnoverRange
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin,
    format_date_or_datetime,
)


class TestUpdateCompany(APITestMixin):
    """Tests for updating a single company."""

    def test_update_company(self):
        """Test company update."""
        company = CompanyFactory(
            name='Foo ltd.',
            trading_names=['name 1', 'name 2'],
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                'name': 'Acme',
                'trading_names': ['new name'],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['name'] == 'Acme'
        assert response_data['trading_names'] == ['new name']

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
        response_data = response.json()
        assert response_data['name'] == update_data['name']
        assert response_data['registered_address_1'] == update_data['registered_address_1']
        assert response_data['registered_address_town'] == update_data['registered_address_town']
        assert response_data['registered_address_country']['id'] == Country.united_states.value.id

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
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
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

    def test_none_address_fields_are_converted_to_blank(self):
        """
        Tests that address charfields are converted to empty strings
        if None values are used in data.
        """
        company = CompanyFactory(
            registered_address_1='lorem',
            registered_address_2='lorem',
            registered_address_town='lorem',
            registered_address_county='lorem',
            registered_address_postcode='lorem',
            registered_address_country_id=Country.united_states.value.id,
            trading_address_1='lorem',
            trading_address_2='lorem',
            trading_address_town='lorem',
            trading_address_county='lorem',
            trading_address_postcode='lorem',
            trading_address_country_id=Country.united_states.value.id,
        )

        none_fields_expected_to_become_blank = [
            'registered_address_2',
            'registered_address_county',
            'registered_address_postcode',
            'trading_address_1',
            'trading_address_2',
            'trading_address_town',
            'trading_address_county',
            'trading_address_postcode',
        ]

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data={
                **{
                    field: None
                    for field in none_fields_expected_to_become_blank
                },
                'trading_address_country': None,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        company.refresh_from_db()

        # check that model fields are empty (not None)
        actual_model_fields = model_to_dict(
            company,
            fields=none_fields_expected_to_become_blank,
        )
        expected_model_fields = {
            field: ''
            for field in none_fields_expected_to_become_blank
        }
        assert actual_model_fields == expected_model_fields

        # check that the response fields are empty strings (not None)
        response_data = response.json()
        actual_response_fields = {
            field: response_data[field]
            for field in none_fields_expected_to_become_blank
        }
        expected_response_fields = expected_model_fields
        assert actual_response_fields == expected_response_fields

    def test_cannot_update_dnb_readonly_fields_if_duns_number_is_set(self):
        """
        Test that if company.duns_number is not blank, the client cannot update the
        fields defined by CompanySerializerV3.Meta.dnb_read_only_fields.
        """
        company = CompanyFactory(
            duns_number='012345678',
            name='name',
            trading_names=['a', 'b', 'c'],
            company_number='company number',
            vat_number='vat number',
            registered_address_1='registered address 1',
            registered_address_2='registered address 2',
            registered_address_town='registered address town',
            registered_address_county='registered address county',
            registered_address_postcode='registered address postcode',
            registered_address_country_id=Country.anguilla.value.id,
            website='website',
            trading_address_1='trading address 1',
            trading_address_2='trading address 2',
            trading_address_town='trading address town',
            trading_address_county='trading address county',
            trading_address_postcode='trading address postcode',
            trading_address_country_id=Country.argentina.value.id,
            business_type_id=BusinessTypeConstant.charity.value.id,
            employee_range_id=EmployeeRange.range_10_to_49.value.id,
            turnover_range_id=TurnoverRange.range_1_34_to_6_7.value.id,
            headquarter_type_id=HeadquarterType.ehq.value.id,
            global_headquarters_id=CompanyFactory(
                headquarter_type_id=HeadquarterType.ghq.value.id,
            ).id,
        )

        data = {
            'name': 'new name',
            'trading_names': ['new trading name'],
            'company_number': 'new company number',
            'vat_number': 'new vat number',
            'registered_address_1': 'new registered address 1',
            'registered_address_2': 'new registered address 2',
            'registered_address_town': 'new registered address town',
            'registered_address_county': 'new registered address county',
            'registered_address_postcode': 'new registered address postcode',
            'registered_address_country': Country.azerbaijan.value.id,
            'website': 'new website',
            'trading_address_1': 'new trading address 1',
            'trading_address_2': 'new trading address 2',
            'trading_address_town': 'new trading address town',
            'trading_address_county': 'new trading address county',
            'trading_address_postcode': 'new trading address postcode',
            'trading_address_country': Country.canada.value.id,
            'business_type': BusinessTypeConstant.community_interest_company.value.id,
            'employee_range': EmployeeRange.range_1_to_9.value.id,
            'turnover_range': TurnoverRange.range_33_5_plus.value.id,
            'headquarter_type': HeadquarterType.ghq.value.id,
            'global_headquarters': company.id,
        }

        assert set(data.keys()) == set(CompanySerializerV3.Meta.dnb_read_only_fields), (
            'It looks like you have changed CompanySerializerV3.Meta.dnb_read_only_fields, '
            'please update this test accordingly.'
        )

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
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
        ),
    )
    def test_validation_error(self, data, expected_error):
        """Test validation scenarios."""
        company = CompanyFactory()

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(
            url,
            data=data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_error

    @pytest.mark.parametrize('field', ('sector',))
    def test_update_null_field_to_null(self, field):
        """
        Tests setting fields to null that are currently null, and are allowed to be null
        when already null.
        """
        company = CompanyFactory(**{f'{field}_id': None})

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
        """
        Tests if adding company that is not a Global HQ as a Global HQ
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
        assert response.json()['global_headquarters'] is None

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
        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
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


class TestAddressesForCompany(APITestMixin):
    """
    Tests related to saving the value of address fields from trading or registered address fields.

    TODO: delete after the migration to address and registered address is completed
    """

    @pytest.mark.parametrize(
        'initial_model_values,data,expected_model_values',
        (
            # address fields populated from trading address fields in data
            (
                {
                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,

                    'trading_address_1': '',
                    'trading_address_2': '',
                    'trading_address_town': '',
                    'trading_address_county': '',
                    'trading_address_postcode': '',
                    'trading_address_country_id': None,
                },
                {
                    'trading_address_1': '1',
                    'trading_address_2': 'Hello st.',
                    'trading_address_town': 'Muckamore',
                    'trading_address_county': 'Antrim',
                    'trading_address_postcode': 'BT41 4QE',
                    'trading_address_country': {'id': Country.ireland.value.id},
                },
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': uuid.UUID(Country.ireland.value.id),
                },
            ),

            # address fields populated from registered address fields in data
            (
                {
                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,

                    'trading_address_1': '',
                    'trading_address_2': '',
                    'trading_address_town': '',
                    'trading_address_county': '',
                    'trading_address_postcode': '',
                    'trading_address_country_id': None,
                },
                {
                    'registered_address_1': '1',
                    'registered_address_2': 'Hello st.',
                    'registered_address_town': 'Muckamore',
                    'registered_address_county': 'Antrim',
                    'registered_address_postcode': 'BT41 4QE',
                    'registered_address_country': {'id': Country.ireland.value.id},
                },
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': uuid.UUID(Country.ireland.value.id),
                },
            ),

            # address fields populated from trading address fields in the model
            (
                {
                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,

                    'trading_address_1': '1',
                    'trading_address_2': 'Hello st.',
                    'trading_address_town': 'Muckamore',
                    'trading_address_county': 'Antrim',
                    'trading_address_postcode': 'BT41 4QE',
                    'trading_address_country_id': Country.ireland.value.id,
                },
                {
                    'registered_address_1': '3',
                },
                {
                    'address_1': '1',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': uuid.UUID(Country.ireland.value.id),
                },
            ),

            # address fields populated from registered address fields in the model
            (
                {
                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,

                    'trading_address_1': '1',
                    'trading_address_2': 'Hello st.',
                    'trading_address_town': 'Muckamore',
                    'trading_address_county': 'Antrim',
                    'trading_address_postcode': 'BT41 4QE',
                    'trading_address_country_id': Country.ireland.value.id,
                },
                {
                    'trading_address_1': '',
                    'trading_address_2': '',
                    'trading_address_town': '',
                    'trading_address_county': '',
                    'trading_address_postcode': '',
                    'trading_address_country': None,
                },
                {
                    'address_1': '2',
                    'address_2': 'Main Road',
                    'address_town': 'London',
                    'address_county': 'Greenwich',
                    'address_postcode': 'SE10 9NN',
                    'address_country_id': uuid.UUID(Country.united_kingdom.value.id),
                },
            ),

            # address is not overridden as no address field was passed in
            (
                {
                    'registered_address_1': '2',
                    'registered_address_2': 'Main Road',
                    'registered_address_town': 'London',
                    'registered_address_county': 'Greenwich',
                    'registered_address_postcode': 'SE10 9NN',
                    'registered_address_country_id': Country.united_kingdom.value.id,

                    'trading_address_1': '',
                    'trading_address_2': '',
                    'trading_address_town': '',
                    'trading_address_county': '',
                    'trading_address_postcode': '',
                    'trading_address_country_id': None,

                    'address_1': '11',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': Country.ireland.value.id,
                },
                {
                    'name': 'other name',
                },
                {

                    'address_1': '11',
                    'address_2': 'Hello st.',
                    'address_town': 'Muckamore',
                    'address_county': 'Antrim',
                    'address_postcode': 'BT41 4QE',
                    'address_country_id': uuid.UUID(Country.ireland.value.id),
                },
            ),
        ),
    )
    def test_update_company_saves_address_correctly(
        self,
        initial_model_values,
        data,
        expected_model_values,
    ):
        """
        Test that the value of address fields are populated from trading address or
        registered address whichever is defined.
        """
        company = CompanyFactory(**initial_model_values)

        url = reverse('api-v3:company:item', kwargs={'pk': company.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        company.refresh_from_db()
        for field, value in expected_model_values.items():
            assert getattr(company, field) == value


class TestArchiveCompany(APITestMixin):
    """Archive company tests."""

    def test_archive_company_no_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'reason': ['This field is required.'],
        }

    def test_archive_company_reason(self):
        """Test company archive."""
        company = CompanyFactory()
        url = reverse('api-v3:company:archive', kwargs={'pk': company.id})
        response = self.api_client.post(url, data={'reason': 'foo'})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived']
        assert response_data['archived_reason'] == 'foo'
        assert response_data['id'] == str(company.id)

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
        response_data = response.json()
        assert response_data['archived']
        assert response_data['archived_reason'] == 'foo'


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
        assert not response.json()['archived']

    def test_unarchive_company(self):
        """Unarchive a company."""
        company = CompanyFactory(
            archived=True, archived_on=now(), archived_reason='foo',
        )
        url = reverse('api-v3:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert not response_data['archived']
        assert response_data['archived_reason'] == ''
        assert response_data['id'] == str(company.id)

    def test_cannot_unarchive_duplicate_company(self):
        """Test that a duplicate company cannot be unarchived."""
        company = DuplicateCompanyFactory()
        url = reverse('api-v3:company:unarchive', kwargs={'pk': company.id})
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            api_settings.NON_FIELD_ERRORS_KEY:
                [
                    'This record is no longer in use and its data has been transferred to another '
                    'record for the following reason: Duplicate record.',
                ],
        }


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


class TestOneListGroupCoreTeam(APITestMixin):
    """Tests for getting the One List Core Team of a company's group."""

    @pytest.mark.parametrize(
        'build_company',
        (
            # as subsidiary
            lambda: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=None),
            ),
            # as single company
            lambda: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=None,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    def test_empty_list(self, build_company):
        """
        Test that if there's no Global Account Manager and no Core Team
        member for a company's Global Headquarters, the endpoint returns
        an empty list.
        """
        company = build_company()

        url = reverse(
            'api-v3:company:one-list-group-core-team',
            kwargs={'pk': company.pk},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.parametrize(
        'build_company',
        (
            # as subsidiary
            lambda gam: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=gam),
            ),
            # as single company
            lambda gam: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=gam,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    def test_with_only_global_account_manager(self, build_company):
        """
        Test that if there is a Global Account Manager but no Core Team
        member for a company's Global Headquarters, the endpoint returns
        a list with only that adviser in it.
        """
        global_account_manager = AdviserFactory()
        company = build_company(global_account_manager)

        url = reverse(
            'api-v3:company:one-list-group-core-team',
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
        'build_company',
        (
            # as subsidiary
            lambda gam: CompanyFactory(
                global_headquarters=CompanyFactory(one_list_account_owner=gam),
            ),
            # as single company
            lambda gam: CompanyFactory(
                global_headquarters=None,
                one_list_account_owner=gam,
            ),
        ),
        ids=('as_subsidiary', 'as_non_subsidiary'),
    )
    @pytest.mark.parametrize(
        'with_global_account_manager',
        (True, False),
        ids=lambda val: f'{"With" if val else "Without"} global account manager',
    )
    def test_with_core_team_members(self, build_company, with_global_account_manager):
        """
        Test that if there are Core Team members for a company's Global Headquarters,
        the endpoint returns a list with these advisers in it.
        """
        team_member_advisers = AdviserFactory.create_batch(
            3,
            first_name=factory.Iterator(
                ('Adam', 'Barbara', 'Chris'),
            ),
        )
        global_account_manager = team_member_advisers[0] if with_global_account_manager else None

        company = build_company(global_account_manager)
        group_global_headquarters = company.global_headquarters or company
        OneListCoreTeamMemberFactory.create_batch(
            len(team_member_advisers),
            company=group_global_headquarters,
            adviser=factory.Iterator(team_member_advisers),
        )

        url = reverse(
            'api-v3:company:one-list-group-core-team',
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
            'api-v3:company:one-list-group-core-team',
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
