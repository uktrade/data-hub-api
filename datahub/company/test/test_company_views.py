from operator import itemgetter

import pytest
import reversion
from django.utils.timezone import now
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.models import CompaniesHouseCompany
from datahub.company.test.factories import CompaniesHouseCompanyFactory, CompanyFactory
from datahub.core.constants import (
    BusinessType, CompanyClassification, Country, HeadquarterType, Sector, UKRegion
)
from datahub.core.test_utils import APITestMixin
from datahub.investment.test.factories import InvestmentProjectFactory


class TestCompany(APITestMixin):
    """Company test case."""

    def test_list_companies(self):
        """List the companies."""
        CompanyFactory()
        CompanyFactory()
        url = reverse('api-v3:company:collection')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_get_company_with_company_number(self):
        """Tests the company item view for a company with a company number.

        Checks that the registered name and registered address are coming from
        CH data.
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

        url = reverse('api-v3:company:item', kwargs={'pk': company.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(company.pk)
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
            'trading_name': 'Trading name',
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
        assert response.data['trading_name'] == 'Trading name'

    def test_promote_a_ch_company(self):
        """Promote a CH company to full company."""
        CompaniesHouseCompanyFactory(company_number=1234567890)

        url = reverse('api-v3:company:collection')
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
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_add_uk_company_without_uk_region(self):
        """Test add new UK without UK region company."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, format='json', data={
            'name': 'Acme',
            'trading_name': None,
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
            'trading_name': None,
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

    def test_add_company_without_address(self):
        """Tests adding a company without a country."""
        url = reverse('api-v3:company:collection')
        response = self.api_client.post(url, {
            'name': 'Acme',
            'trading_name': None,
            'business_type': BusinessType.company.value.id,
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
            'business_type': BusinessType.company.value.id,
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
            'business_type': BusinessType.company.value.id,
            'registered_address_1': '75 Stramford Road',
            'registered_address_town': 'London',
            'registered_address_country': Country.united_kingdom.value.id,
            'uk_region': UKRegion.england.value.id,
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[field] == ['This field is required.']

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
        assert entry['timestamp'] == changed_datetime.isoformat()
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

    def test_ch_company_cannot_be_written(self):
        """Test CH company POST is not allowed."""
        url = reverse('api-v3:ch-company:collection')
        response = self.api_client.post(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
