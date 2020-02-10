import uuid

import pytest
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.constants import Country, Sector, UKRegion
from datahub.core.test_utils import APITestMixin, format_date_or_datetime
from datahub.omis.market.models import Market
from datahub.omis.order.constants import OrderStatus, VATStatus
from datahub.omis.order.models import CancellationReason, ServiceType
from datahub.omis.order.test.factories import (
    OrderAssigneeCompleteFactory,
    OrderAssigneeFactory,
    OrderCancelledFactory,
    OrderCompleteFactory,
    OrderFactory,
    OrderPaidFactory,
    OrderWithAcceptedQuoteFactory,
    OrderWithOpenQuoteFactory,
)


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestAddOrder(APITestMixin):
    """Add Order details test case."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_success_complete(self):
        """Test a successful call to create an Order with all possible fields."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.france.value
        uk_region = UKRegion.jersey.value
        sector = Sector.renewable_energy_wind.value
        service_type = ServiceType.objects.filter(disabled_on__isnull=True).first()

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
                'sector': {'id': sector.id},
                'uk_region': {'id': uk_region.id},
                'service_types': [
                    {'id': service_type.pk},
                ],
                'description': 'Description test',
                'contacts_not_to_approach': 'Contacts not to approach details',
                'further_info': 'Additional notes',
                'existing_agents': 'Contacts in the market',
                'delivery_date': '2017-04-20',
                'po_number': 'PO 123',
                'vat_status': VATStatus.EU,
                'vat_number': '01234566789',
                'vat_verified': True,
                'billing_address_1': 'Apt 1',
                'billing_address_2': 'London Street',
                'billing_address_town': 'London',
                'billing_address_county': 'London',
                'billing_address_postcode': 'SW1A1AA',
                'billing_address_country': Country.united_kingdom.value.id,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'reference': response.json()['reference'],
            'status': OrderStatus.draft,
            'created_on': '2017-04-18T13:00:00Z',
            'created_by': {
                'id': str(self.user.pk),
                'name': self.user.name,
            },
            'modified_on': '2017-04-18T13:00:00Z',
            'modified_by': {
                'id': str(self.user.pk),
                'name': self.user.name,
            },
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name,
            },
            'primary_market': {
                'id': str(country.id),
                'name': country.name,
            },
            'sector': {
                'id': sector.id,
                'name': sector.name,
            },
            'uk_region': {
                'id': uk_region.id,
                'name': uk_region.name,
            },
            'service_types': [
                {
                    'id': str(service_type.pk),
                    'name': service_type.name,
                },
            ],
            'description': 'Description test',
            'contacts_not_to_approach': 'Contacts not to approach details',
            'product_info': '',
            'further_info': 'Additional notes',
            'existing_agents': 'Contacts in the market',
            'permission_to_approach_contacts': '',
            'delivery_date': '2017-04-20',
            'contact_email': '',
            'contact_phone': '',
            'po_number': 'PO 123',
            'discount_value': 0,
            'vat_status': VATStatus.EU,
            'vat_number': '01234566789',
            'vat_verified': True,
            'net_cost': 0,
            'subtotal_cost': 0,
            'vat_cost': 0,
            'total_cost': 0,
            'billing_company_name': '',
            'billing_contact_name': '',
            'billing_email': '',
            'billing_phone': '',
            'billing_address_1': 'Apt 1',
            'billing_address_2': 'London Street',
            'billing_address_town': 'London',
            'billing_address_county': 'London',
            'billing_address_postcode': 'SW1A1AA',
            'billing_address_country': {
                'id': str(Country.united_kingdom.value.id),
                'name': Country.united_kingdom.value.name,
            },
            'archived_documents_url_path': '',
            'paid_on': None,
            'completed_by': None,
            'completed_on': None,
            'cancelled_by': None,
            'cancelled_on': None,
            'cancellation_reason': None,
        }

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_success_minimal(self):
        """Test a successful call to create an Order without optional fields."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.france.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['sector'] is None
        assert response.json()['uk_region'] == {  # populated automatically from the company
            'id': str(company.uk_region.id),
            'name': company.uk_region.name,
        }
        assert response.json()['service_types'] == []
        assert response.json()['description'] == ''
        assert response.json()['contacts_not_to_approach'] == ''
        assert response.json()['delivery_date'] is None
        assert response.json()['po_number'] == ''
        assert response.json()['vat_status'] == ''
        assert response.json()['vat_number'] == ''
        assert response.json()['vat_verified'] is None
        assert response.json()['discount_value'] == 0
        assert response.json()['net_cost'] == 0
        assert response.json()['subtotal_cost'] == 0
        assert response.json()['vat_cost'] == 0
        assert response.json()['total_cost'] == 0
        assert response.json()['billing_company_name'] == ''
        assert response.json()['billing_contact_name'] == ''
        assert response.json()['billing_email'] == ''
        assert response.json()['billing_phone'] == ''
        assert response.json()['billing_address_1'] == ''
        assert response.json()['billing_address_2'] == ''
        assert response.json()['billing_address_town'] == ''
        assert response.json()['billing_address_county'] == ''
        assert response.json()['billing_address_postcode'] == ''
        assert not response.json()['billing_address_country']

    def test_fails_if_contact_not_from_company(self):
        """
        Test that if the contact does not work at the company specified, the validation fails.
        """
        company = CompanyFactory()
        contact = ContactFactory()  # doesn't work at `company`
        country = Country.france.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': ['The contact does not work at the given company.'],
        }

    def test_general_validation(self):
        """Test create an Order general validation."""
        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ['This field is required.'],
            'contact': ['This field is required.'],
            'primary_market': ['This field is required.'],
        }

    @freeze_time('2017-11-23 11:00:00.000000')
    def test_fails_if_service_type_disabled(self):
        """Test that if a service type specified is disabled, the creation fails."""
        company = CompanyFactory()
        disabled_service_type = ServiceType.objects.filter(disabled_on__lte=now()).first()

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': ContactFactory(company=company).pk},
                'primary_market': {'id': Country.france.value.id},
                'service_types': [
                    {'id': disabled_service_type.pk},
                ],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'service_types': [f'"{disabled_service_type.name}" disabled.'],
        }

    def test_fails_if_primary_market_disabled(self):
        """Test that if the primary market is disabled, the creation fails."""
        company = CompanyFactory()
        disabled_country = Market.objects.filter(disabled_on__lte=now()).first().country

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': ContactFactory(company=company).pk},
                'primary_market': {'id': disabled_country.pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'primary_market': [f'"{disabled_country.name}" disabled.'],
        }

    def test_fails_if_primary_market_doesnt_exist(self):
        """
        Test that if the primary market does not have an OMIS market record defined,
        the creation fails.
        """
        company = CompanyFactory()
        market = Market.objects.first()
        non_market_country = market.country

        market.delete()

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': ContactFactory(company=company).pk},
                'primary_market': {'id': non_market_country.pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'primary_market': [
                f"The OMIS market for country '{non_market_country}' doesn't exist.",
            ],
        }

    def test_cannot_post_legacy_fields(self):
        """Test that if legacy fields are passed in when creating an order, they get ignored."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.france.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
                'product_info': 'lorem ipsum',
                'permission_to_approach_contacts': 'lorem ipsum',
                'archived_documents_url_path': '/documents/123',
                'billing_contact_name': 'John Doe',
                'billing_email': 'JohnDoe@example.com',
                'billing_phone': '0123456789',
                'contact_email': 'JohnDoe@example.com',
                'contact_phone': '0123456789',
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['product_info'] == ''
        assert response.json()['permission_to_approach_contacts'] == ''
        assert response.json()['archived_documents_url_path'] == ''
        assert response.json()['billing_contact_name'] == ''
        assert response.json()['billing_email'] == ''
        assert response.json()['billing_phone'] == ''
        assert response.json()['contact_email'] == ''
        assert response.json()['contact_phone'] == ''

    @pytest.mark.parametrize(
        'vat_status',
        (VATStatus.OUTSIDE_EU, VATStatus.UK),
    )
    def test_vat_number_and_verified_reset_if_vat_status_not_eu(self, vat_status):
        """
        Test that if vat_number and vat_verified are set but vat_status != 'eu',
        they are set to '' and None as they only make sense if company in 'eu'.
        """
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.canada.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
                'vat_status': vat_status,
                'vat_number': '0123456789',
                'vat_verified': True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['vat_status'] == vat_status
        assert response.json()['vat_number'] == ''
        assert response.json()['vat_verified'] is None

    def test_fails_with_incomplete_billing_address(self):
        """
        Test that if one of the billing address fields is set, all the other required
        billing fields should be set as well.
        """
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.france.value

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
                'billing_address_2': 'London Street',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'billing_address_1': ['This field is required.'],
            'billing_address_town': ['This field is required.'],
            'billing_address_country': ['This field is required.'],
        }


class TestGeneralChangeOrder(APITestMixin):
    """Tests for changing an order not related to any particular status."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_uk_region_not_populated_on_change(self):
        """
        Test that if order.uk_region is None,
        it doesn't get populated automatically on change.
        """
        order = OrderFactory(
            vat_status=VATStatus.OUTSIDE_EU,
            uk_region_id=None,
        )
        assert not order.uk_region
        assert order.company.uk_region

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url, {'description': 'Updated description'},
        )

        order.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert not response.json()['uk_region']

    def test_fails_if_contact_not_from_company(self):
        """
        Test that if the contact does not work at the company specified, the validation fails.
        """
        order = OrderFactory()
        other_contact = ContactFactory()  # doesn't work at `order.company`

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'contact': {'id': other_contact.pk},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': ['The contact does not work at the given company.'],
        }

    def test_general_validation(self):
        """Test general validation."""
        order = OrderFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'contact': {'id': '00000000-0000-0000-0000-000000000000'},
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': [
                'Invalid pk "00000000-0000-0000-0000-000000000000" - object does not exist.',
            ],
        }

    @freeze_time('2017-11-23 11:00:00.000000')
    def test_fails_if_service_type_disabled(self):
        """Test that if a service type specified is disabled, the update fails."""
        order = OrderFactory()
        disabled_service_type = ServiceType.objects.filter(disabled_on__lte=now()).first()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'service_types': [
                    {'id': disabled_service_type.pk},
                ],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'service_types': [f'"{disabled_service_type.name}" disabled.'],
        }

    @freeze_time('2017-01-01 11:00:00.000000')
    def test_can_update_service_type_with_another_disabled_if_wasnt_at_creation_time(self):
        """
        Test that if I have an order created on 01/01/2017
        with a service type which got disabled on 10/01/2017

        If I update the order
        with a service type that got disabled on  01/02/2017

        I can still update it as the service type was not disabled at the time
        the order got created.
        """
        disabled_in_jan, disabled_in_feb = ServiceType.objects.all()[:2]

        disabled_in_jan.disabled_on = dateutil_parse('2017-01-10T11:00:00Z')
        disabled_in_jan.save()

        disabled_in_feb.disabled_on = dateutil_parse('2017-02-01T11:00:00Z')
        disabled_in_feb.save()

        order = OrderFactory(service_types=[disabled_in_jan])

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'service_types': [
                    {'id': disabled_in_feb.pk},
                ],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['service_types'] == [
            {
                'id': str(disabled_in_feb.pk),
                'name': disabled_in_feb.name,
            },
        ]

    def test_cannot_change_readonly_fields(self):
        """Test that if readonly fields are passed in when updating an order, they get ignored."""
        order = OrderFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'status': OrderStatus.complete,
                'product_info': 'Updated product info',
                'permission_to_approach_contacts': 'Updated permission to approach contacts',
                'contact_email': 'updated-email@email.com',
                'contact_phone': '1234',
                'discount_value': 99999,
                'net_cost': 99999,
                'subtotal_cost': 99999,
                'vat_cost': 99999,
                'total_cost': 99999,
                'archived_documents_url_path': '/documents/123',
                'paid_on': now().isoformat(),
                'completed_by': order.created_by.pk,
                'completed_on': now().isoformat(),
                'cancelled_by': order.created_by.pk,
                'cancelled_on': now().isoformat(),
                'cancellation_reason': {
                    'id': uuid.uuid4(),
                },
                'billing_company_name': 'New Corp',
                'billing_contact_name': 'John Doe',
                'billing_email': 'JohnDoe@example.com',
                'billing_phone': '0123456789',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == OrderStatus.draft
        assert response.json()['product_info'] != 'Updated product info'
        assert response.json()['permission_to_approach_contacts'] != \
            'Updated permission to approach contacts'
        assert response.json()['contact_email'] != 'updated-email@email.com'
        assert response.json()['contact_phone'] != '1234'
        assert response.json()['discount_value'] != 99999
        assert response.json()['net_cost'] != 99999
        assert response.json()['subtotal_cost'] != 99999
        assert response.json()['vat_cost'] != 99999
        assert response.json()['total_cost'] != 99999
        assert not response.json()['archived_documents_url_path']
        assert not response.json()['paid_on']
        assert not response.json()['completed_by']
        assert not response.json()['completed_on']
        assert not response.json()['cancelled_by']
        assert not response.json()['cancelled_on']
        assert not response.json()['cancellation_reason']
        assert response.json()['billing_company_name'] != 'New Corp'
        assert response.json()['billing_contact_name'] != 'John Doe'
        assert response.json()['billing_email'] != 'JohnDoe@example.com'
        assert response.json()['billing_phone'] != '0123456789'

    @pytest.mark.parametrize(
        'vat_status',
        (VATStatus.OUTSIDE_EU, VATStatus.UK),
    )
    def test_vat_number_and_verified_reset_if_vat_status_not_eu(self, vat_status):
        """
        Test that if vat_number and vat_verified are set but vat_status != 'eu',
        they are set to '' and None as they only make sense if company in 'eu'.
        """
        order = OrderFactory(
            vat_status=VATStatus.EU,
            vat_number='0123456789',
            vat_verified=True,
        )

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {'vat_status': vat_status},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['vat_status'] == vat_status
        assert response.json()['vat_number'] == ''
        assert response.json()['vat_verified'] is None

    def test_fails_with_incomplete_billing_address(self):
        """
        Test that if one of the billing address fields is set, all the other required
        billing fields should be set as well.
        """
        order = OrderFactory(
            billing_address_1='',
            billing_address_2='',
            billing_address_country_id=None,
            billing_address_county='',
            billing_address_postcode='',
            billing_address_town='',
        )
        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'billing_address_2': 'London Street',
            },
        )

        order.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'billing_address_1': ['This field is required.'],
            'billing_address_town': ['This field is required.'],
            'billing_address_country': ['This field is required.'],
        }


class TestChangeOrderInDraft(APITestMixin):
    """Tests for changing an order when it's in draft."""

    @freeze_time('2017-04-18 13:00:00.000000')
    def test_can_change_allowed_fields(self):
        """Test changing an existing order."""
        order = OrderFactory(
            vat_status=VATStatus.OUTSIDE_EU,
            uk_region_id=UKRegion.alderney.value.id,
        )
        new_contact = ContactFactory(company=order.company)
        new_sector = Sector.renewable_energy_wind.value
        new_uk_region = UKRegion.channel_islands.value
        new_service_type = ServiceType.objects.filter(disabled_on__isnull=True).first()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'contact': {'id': new_contact.pk},
                'sector': {'id': new_sector.id},
                'uk_region': {'id': new_uk_region.id},
                'service_types': [
                    {'id': str(new_service_type.pk)},
                ],
                'description': 'Updated description',
                'contacts_not_to_approach': 'Updated contacts not to approach',
                'further_info': 'Updated additional notes',
                'existing_agents': 'Updated contacts in the market',
                'delivery_date': '2017-04-21',
                'po_number': 'NEW PO 321',
                'vat_status': VATStatus.EU,
                'vat_number': 'new vat number',
                'vat_verified': False,
                'billing_address_1': 'Apt 1',
                'billing_address_2': 'London Street',
                'billing_address_town': 'London',
                'billing_address_county': 'London',
                'billing_address_postcode': 'SW1A1AA',
                'billing_address_country': Country.united_kingdom.value.id,
            },
        )

        order.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(order.pk),
            'reference': order.reference,
            'status': OrderStatus.draft,
            'created_on': '2017-04-18T13:00:00Z',
            'created_by': {
                'id': str(order.created_by.pk),
                'name': order.created_by.name,
            },
            'modified_on': '2017-04-18T13:00:00Z',
            'modified_by': {
                'id': str(self.user.pk),
                'name': self.user.name,
            },
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name,
            },
            'contact': {
                'id': str(new_contact.pk),
                'name': new_contact.name,
            },
            'primary_market': {
                'id': str(order.primary_market.pk),
                'name': order.primary_market.name,
            },
            'sector': {
                'id': new_sector.id,
                'name': new_sector.name,
            },
            'uk_region': {
                'id': new_uk_region.id,
                'name': new_uk_region.name,
            },
            'service_types': [
                {
                    'id': str(new_service_type.pk),
                    'name': new_service_type.name,
                },
            ],
            'description': 'Updated description',
            'contacts_not_to_approach': 'Updated contacts not to approach',
            'product_info': order.product_info,
            'further_info': 'Updated additional notes',
            'existing_agents': 'Updated contacts in the market',
            'permission_to_approach_contacts': order.permission_to_approach_contacts,
            'delivery_date': '2017-04-21',
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'po_number': 'NEW PO 321',
            'discount_value': order.discount_value,
            'vat_status': VATStatus.EU,
            'vat_number': 'new vat number',
            'vat_verified': False,
            'net_cost': order.net_cost,
            'subtotal_cost': order.subtotal_cost,
            'vat_cost': order.vat_cost,
            'total_cost': order.total_cost,
            'billing_company_name': order.billing_company_name,
            'billing_contact_name': order.billing_contact_name,
            'billing_email': order.billing_email,
            'billing_phone': order.billing_phone,
            'billing_address_1': 'Apt 1',
            'billing_address_2': 'London Street',
            'billing_address_town': 'London',
            'billing_address_county': 'London',
            'billing_address_postcode': 'SW1A1AA',
            'billing_address_country': {
                'id': str(Country.united_kingdom.value.id),
                'name': Country.united_kingdom.value.name,
            },
            'archived_documents_url_path': '',
            'paid_on': None,
            'completed_by': None,
            'completed_on': None,
            'cancelled_by': None,
            'cancelled_on': None,
            'cancellation_reason': None,
        }

    @pytest.mark.parametrize(
        'field,value',
        (
            ('company', lambda o: CompanyFactory().pk),
            ('primary_market', Country.greece.value.id),
        ),
    )
    def test_cannot_change_disallowed_fields(self, field, value):
        """Test that disallowed fields cannot be changed."""
        order = OrderFactory()
        value = value(order) if callable(value) else value

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {field: value})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {field: ['This field cannot be changed at this stage.']}

    def test_ok_with_unchanged_disallowed_fields(self):
        """Test that disallowed fields can be passed in if their values don't change."""
        order = OrderFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'company': order.company.pk,
                'primary_market': order.primary_market.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK


class TestChangeOrderInQuoteStatuses(APITestMixin):
    """
    Tests for changing an order when it's in quote_awaiting_acceptance
    or quote_accepted.
    """

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderWithOpenQuoteFactory,
            OrderWithAcceptedQuoteFactory,
        ),
    )
    def test_can_change_allowed_fields(self, order_factory):
        """Test that allowed fields can be changed."""
        order = order_factory(
            vat_status=VATStatus.EU,
            vat_number='01234566789',
            vat_verified=True,
        )
        new_contact = ContactFactory(company=order.company)

        data = {
            'billing_address_1': 'New billing address 1',
            'billing_address_2': 'New billing address 2',
            'billing_address_town': 'New billing town',
            'billing_address_county': 'New billing county',
            'billing_address_postcode': 'New billing postcode',
            'billing_address_country': Country.france.value.id,
            'vat_status': VATStatus.EU,
            'vat_number': '987654321',
            'vat_verified': False,
            'po_number': 'New po number',

            'contact': new_contact.pk,
        }

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert {
            k: v for k, v in response.json().items() if k in data
        } == {
            **data,
            'billing_address_country': {
                'id': Country.france.value.id,
                'name': Country.france.value.name,
            },
            'contact': {
                'id': str(new_contact.pk),
                'name': new_contact.name,
            },
        }

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderWithOpenQuoteFactory,
            OrderWithAcceptedQuoteFactory,
        ),
    )
    @pytest.mark.parametrize(
        'field,value',
        (
            ('company', lambda o: CompanyFactory().pk),
            ('primary_market', Country.greece.value.id),

            (
                'service_types',
                lambda o: [ServiceType.objects.filter(disabled_on__isnull=True).first().id],
            ),
            ('uk_region', UKRegion.jersey.value.id),
            ('sector', Sector.renewable_energy_wind.value.id),
            ('existing_agents', 'loremm ipsum'),
            ('further_info', 'lorem ipsum'),
            ('contacts_not_to_approach', 'lorem ipsum'),
            ('description', 'lorem ipsum'),
            ('delivery_date', '2017-04-20'),
        ),
    )
    def test_cannot_change_disallowed_fields(self, order_factory, field, value):
        """Test that disallowed fields cannot be changed."""
        order = order_factory()
        value = value(order) if callable(value) else value

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {field: value})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {field: ['This field cannot be changed at this stage.']}

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderWithOpenQuoteFactory,
            OrderWithAcceptedQuoteFactory,
        ),
    )
    def test_ok_with_unchanged_disallowed_fields(self, order_factory):
        """Test that disallowed fields can be passed in if their values don't change."""
        order = order_factory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'company': order.company.pk,
                'primary_market': order.primary_market.pk,

                'service_types': order.service_types.values_list('id', flat=True),
                'uk_region': order.uk_region.pk,
                'sector': order.sector.pk,
                'existing_agents': order.existing_agents,
                'further_info': order.further_info,
                'contacts_not_to_approach': order.contacts_not_to_approach,
                'description': order.description,
                'delivery_date': order.delivery_date.isoformat(),
            },
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        'field,value',
        (
            ('billing_address_1', 'New billing address 1'),
            ('billing_address_2', 'New billing address 2'),
            ('billing_address_town', 'New billing town'),
            ('billing_address_county', 'New billing county'),
            ('billing_address_postcode', 'New billing postcode'),
            ('billing_address_country', Country.france.value.id),
            ('vat_status', VATStatus.EU),
            ('vat_number', '987654321'),
            ('vat_verified', False),
            ('po_number', 'New po number'),
        ),
    )
    def test_new_invoice_generated_if_quote_accepted(self, field, value):
        """
        Test that if the order is in status 'Quote accepted' and one of the
        billing fields has changed, a new invoice is generated.
        """
        order = OrderWithAcceptedQuoteFactory(
            vat_status=VATStatus.EU,
            vat_number='01234566789',
            vat_verified=True,
        )
        old_invoice = order.invoice

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {field: value})
        assert response.status_code == status.HTTP_200_OK

        order.refresh_from_db()
        assert order.invoice != old_invoice

        new_value = getattr(order.invoice, field)
        if hasattr(new_value, 'pk'):
            new_value = str(new_value.pk)
        assert new_value == value

    def test_pricing_on_invoice_changed_if_quote_accepted(self):
        """
        Test that if the order is in status 'Quote accepted'
        and one of the vat fields change, the pricing on the new invoice
        get updated.
        """
        order = OrderWithAcceptedQuoteFactory(
            vat_status=VATStatus.EU,
            vat_number='01234566789',
            vat_verified=True,
        )
        old_invoice = order.invoice

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {'vat_verified': False})
        assert response.status_code == status.HTTP_200_OK

        order.refresh_from_db()
        new_invoice = order.invoice

        assert new_invoice != old_invoice
        assert new_invoice.vat_status == old_invoice.vat_status
        assert new_invoice.vat_number == old_invoice.vat_number
        assert new_invoice.vat_verified != old_invoice.vat_verified
        assert new_invoice.net_cost == old_invoice.net_cost
        assert new_invoice.subtotal_cost == old_invoice.subtotal_cost
        assert new_invoice.vat_cost != old_invoice.vat_cost
        assert new_invoice.vat_cost > 0
        assert new_invoice.total_cost > old_invoice.total_cost

    @pytest.mark.parametrize(
        'order_factory,data',
        (
            (OrderWithOpenQuoteFactory, {'vat_verified': False}),
            (
                OrderWithOpenQuoteFactory,
                {'contact': lambda o: ContactFactory(company=o.company).pk},
            ),
            (
                OrderWithAcceptedQuoteFactory,
                {'contact': lambda o: ContactFactory(company=o.company).pk},
            ),
            (
                OrderPaidFactory,
                {'contact': lambda o: ContactFactory(company=o.company).pk},
            ),
        ),
    )
    def test_invoice_not_generated(self, order_factory, data):
        """Test that changing `data` does not generate a new invoice."""
        order = order_factory(
            vat_status=VATStatus.EU,
            vat_number='01234566789',
            vat_verified=True,
        )
        old_invoice = order.invoice

        data = {
            field: value(order) if callable(value) else value
            for field, value in data.items()
        }
        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK

        order.refresh_from_db()
        assert old_invoice == order.invoice


class TestChangeOrderInPaid(APITestMixin):
    """Tests for changing an order when it's in paid."""

    def test_can_change_allowed_fields(self):
        """Test that allowed fields can be changed."""
        order = OrderPaidFactory()
        new_contact = ContactFactory(company=order.company)

        data = {
            'contact': new_contact.pk,
        }

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['contact'] == {
            'id': str(new_contact.pk),
            'name': new_contact.name,
        }

    @pytest.mark.parametrize(
        'field,value',
        (
            ('company', lambda o: CompanyFactory().pk),
            ('primary_market', Country.greece.value.id),

            (
                'service_types',
                lambda o: [ServiceType.objects.filter(disabled_on__isnull=True).first().id],
            ),
            ('uk_region', UKRegion.jersey.value.id),
            ('sector', Sector.renewable_energy_wind.value.id),
            ('existing_agents', 'loremm ipsum'),
            ('further_info', 'lorem ipsum'),
            ('contacts_not_to_approach', 'lorem ipsum'),
            ('description', 'lorem ipsum'),
            ('delivery_date', '2017-04-20'),

            ('billing_address_1', 'New billing address 1'),
            ('billing_address_2', 'New billing address 2'),
            ('billing_address_town', 'New billing town'),
            ('billing_address_county', 'New billing county'),
            ('billing_address_postcode', 'New billing postcode'),
            ('billing_address_country', Country.france.value.id),
            ('vat_status', VATStatus.UK),
            ('vat_number', '987654321'),
            ('vat_verified', False),
            ('po_number', 'New po number'),
        ),
    )
    def test_cannot_change_disallowed_fields(self, field, value):
        """Test that disallowed fields cannot be changed."""
        order = OrderPaidFactory()
        value = value(order) if callable(value) else value

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {field: value})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {field: ['This field cannot be changed at this stage.']}

    def test_ok_with_unchanged_disallowed_fields(self):
        """Test that disallowed fields can be passed in if their values don't change."""
        order = OrderPaidFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})

        response = self.api_client.patch(
            url,
            {
                'company': order.company.pk,
                'primary_market': order.primary_market.pk,

                'service_types': order.service_types.values_list('id', flat=True),
                'uk_region': order.uk_region.pk,
                'sector': order.sector.pk,
                'existing_agents': order.existing_agents,
                'further_info': order.further_info,
                'contacts_not_to_approach': order.contacts_not_to_approach,
                'description': order.description,
                'delivery_date': order.delivery_date.isoformat(),

                'billing_address_1': order.billing_address_1,
                'billing_address_2': order.billing_address_2,
                'billing_address_town': order.billing_address_town,
                'billing_address_county': order.billing_address_county,
                'billing_address_postcode': order.billing_address_postcode,
                'billing_address_country': order.billing_address_country.pk,
                'vat_status': order.vat_status,
                'vat_number': order.vat_number,
                'vat_verified': order.vat_verified,
                'po_number': order.po_number,
            },
        )
        assert response.status_code == status.HTTP_200_OK


class TestChangeOrderInEndStatuses(APITestMixin):
    """Tests for changing an order when it's in complete or cancelled."""

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderCompleteFactory,
            OrderCancelledFactory,
        ),
    )
    @pytest.mark.parametrize(
        'field,value',
        (
            ('company', lambda o: CompanyFactory().pk),
            ('primary_market', Country.greece.value.id),

            (
                'service_types',
                lambda o: [ServiceType.objects.filter(disabled_on__isnull=True).first().id],
            ),
            ('uk_region', UKRegion.jersey.value.id),
            ('sector', Sector.renewable_energy_wind.value.id),
            ('existing_agents', 'loremm ipsum'),
            ('further_info', 'lorem ipsum'),
            ('contacts_not_to_approach', 'lorem ipsum'),
            ('description', 'lorem ipsum'),
            ('delivery_date', '2017-04-20'),

            ('billing_address_1', 'New billing address 1'),
            ('billing_address_2', 'New billing address 2'),
            ('billing_address_town', 'New billing town'),
            ('billing_address_county', 'New billing county'),
            ('billing_address_postcode', 'New billing postcode'),
            ('billing_address_country', Country.france.value.id),
            ('vat_status', VATStatus.UK),
            ('vat_number', '987654321'),
            ('vat_verified', False),
            ('po_number', 'New po number'),

            ('contact', lambda o: ContactFactory(company=o.company).pk),
        ),
    )
    def test_cannot_change_disallowed_fields(self, order_factory, field, value):
        """Test that disallowed fields cannot be changed."""
        order = order_factory()
        value = value(order) if callable(value) else value

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {field: value})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {field: ['This field cannot be changed at this stage.']}

    @pytest.mark.parametrize(
        'order_factory',
        (
            OrderCompleteFactory,
            OrderCancelledFactory,
        ),
    )
    def test_ok_with_unchanged_disallowed_fields(self, order_factory):
        """Test that disallowed fields can be passed in if their values don't change."""
        order = order_factory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})

        response = self.api_client.patch(
            url,
            {
                'company': order.company.pk,
                'primary_market': order.primary_market.pk,

                'service_types': order.service_types.values_list('id', flat=True),
                'uk_region': order.uk_region.pk,
                'sector': order.sector.pk,
                'existing_agents': order.existing_agents,
                'further_info': order.further_info,
                'contacts_not_to_approach': order.contacts_not_to_approach,
                'description': order.description,
                'delivery_date': order.delivery_date.isoformat(),

                'billing_address_1': order.billing_address_1,
                'billing_address_2': order.billing_address_2,
                'billing_address_town': order.billing_address_town,
                'billing_address_county': order.billing_address_county,
                'billing_address_postcode': order.billing_address_postcode,
                'billing_address_country': order.billing_address_country.pk,
                'vat_status': order.vat_status,
                'vat_number': order.vat_number,
                'vat_verified': order.vat_verified,
                'po_number': order.po_number,

                'contact': order.contact.pk,
            },
        )
        assert response.status_code == status.HTTP_200_OK


class TestMarkOrderAsComplete(APITestMixin):
    """Test cases for marking an order as complete."""

    @freeze_time('2017-04-18 13:00')
    @pytest.mark.parametrize(
        'allowed_status',
        (OrderStatus.paid,),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """Test marking an order as complete."""
        order = OrderPaidFactory(status=allowed_status, assignees=[])
        OrderAssigneeCompleteFactory(order=order)

        url = reverse('api-v3:omis:order:complete', kwargs={'pk': order.pk})
        response = self.api_client.post(url, {})

        expected_completed_on = dateutil_parse('2017-04-18T13:00Z')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == OrderStatus.complete
        assert response.json()['completed_on'] == format_date_or_datetime(expected_completed_on)
        assert response.json()['completed_by'] == {
            'id': str(self.user.pk),
            'name': self.user.name,
        }

        order.refresh_from_db()
        assert order.status == OrderStatus.complete
        assert order.completed_on == expected_completed_on
        assert order.completed_by == self.user

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.draft,
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_409_if_order_not_in_allowed_status(self, disallowed_status):
        """
        Test that if the order is in a disallowed status, the order cannot be marked as complete.
        """
        order = OrderPaidFactory(status=disallowed_status, assignees=[])
        OrderAssigneeCompleteFactory(order=order)

        url = reverse('api-v3:omis:order:complete', kwargs={'pk': order.pk})
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_409_CONFLICT
        order.refresh_from_db()
        assert order.status == disallowed_status

    def test_400_if_not_all_actual_time_set(self):
        """
        Test that if not all assignee actual time fields have been set,
        a validation error is raised and the call fails.
        """
        order = OrderPaidFactory(status=OrderStatus.paid, assignees=[])
        OrderAssigneeCompleteFactory(order=order)
        OrderAssigneeFactory(order=order)

        url = reverse('api-v3:omis:order:complete', kwargs={'pk': order.pk})
        response = self.api_client.post(url, {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': (
                'You must set the actual time for all assignees to complete this order.'
            ),
        }


class TestCancelOrder(APITestMixin):
    """Test cases for cancelling an order."""

    @freeze_time('2017-04-18 13:00')
    @pytest.mark.parametrize(
        'allowed_status',
        (OrderStatus.draft, OrderStatus.quote_awaiting_acceptance),
    )
    def test_ok_if_order_in_allowed_status(self, allowed_status):
        """Test cancelling an order."""
        reason = CancellationReason.objects.order_by('?').first()
        order = OrderFactory(status=allowed_status)

        url = reverse('api-v3:omis:order:cancel', kwargs={'pk': order.pk})
        response = self.api_client.post(
            url,
            {
                'cancellation_reason': {
                    'id': reason.pk,
                },
            },
        )

        expected_cancelled_on = dateutil_parse('2017-04-18T13:00Z')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == OrderStatus.cancelled
        assert response.json()['cancelled_on'] == format_date_or_datetime(expected_cancelled_on)
        assert response.json()['cancellation_reason'] == {
            'id': str(reason.pk),
            'name': reason.name,
        }
        assert response.json()['cancelled_by'] == {
            'id': str(self.user.pk),
            'name': self.user.name,
        }

        order.refresh_from_db()
        assert order.status == OrderStatus.cancelled
        assert order.cancelled_on == expected_cancelled_on
        assert order.cancellation_reason == reason
        assert order.cancelled_by == self.user

    @pytest.mark.parametrize(
        'disallowed_status',
        (
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        ),
    )
    def test_409_if_order_not_in_allowed_status(self, disallowed_status):
        """
        Test that if the order is in a disallowed status, the order cannot be cancelled.
        """
        reason = CancellationReason.objects.order_by('?').first()
        order = OrderFactory(status=disallowed_status)

        url = reverse('api-v3:omis:order:cancel', kwargs={'pk': order.pk})
        response = self.api_client.post(
            url,
            {
                'cancellation_reason': {
                    'id': reason.pk,
                },
            },
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        order.refresh_from_db()
        assert order.status == disallowed_status

    @pytest.mark.parametrize(
        'data,errors',
        (
            (
                {},
                {'cancellation_reason': ['This field is required.']},
            ),
            (
                {'cancellation_reason': {'id': '2f68875c-35a5-4c3d-8160-9ddc104260c2'}},
                {'cancellation_reason': [
                    'Invalid pk "2f68875c-35a5-4c3d-8160-9ddc104260c2" - object does not exist.',
                ]},
            ),
        ),
    )
    def test_validation_errors(self, data, errors):
        """
        Test that if cancellation_reason is invalid, the endpoint returns 400.
        """
        order = OrderFactory(status=OrderStatus.draft)

        url = reverse('api-v3:omis:order:cancel', kwargs={'pk': order.pk})
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors


class TestViewOrderDetails(APITestMixin):
    """View order details test case."""

    def test_get(self):
        """Test getting an existing order."""
        order = OrderFactory(
            archived_documents_url_path='/documents/123',
        )

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(order.pk),
            'reference': order.reference,
            'status': OrderStatus.draft,
            'created_on': format_date_or_datetime(order.created_on),
            'created_by': {
                'id': str(order.created_by.pk),
                'name': order.created_by.name,
            },
            'modified_on': format_date_or_datetime(order.modified_on),
            'modified_by': {
                'id': str(order.modified_by.pk),
                'name': order.modified_by.name,
            },
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name,
            },
            'contact': {
                'id': str(order.contact.pk),
                'name': order.contact.name,
            },
            'primary_market': {
                'id': str(order.primary_market.pk),
                'name': order.primary_market.name,
            },
            'sector': {
                'id': str(order.sector.id),
                'name': order.sector.name,
            },
            'uk_region': {
                'id': str(order.uk_region.id),
                'name': order.uk_region.name,
            },
            'service_types': [
                {
                    'id': str(service_type.pk),
                    'name': service_type.name,
                } for service_type in order.service_types.all()
            ],
            'description': order.description,
            'contacts_not_to_approach': order.contacts_not_to_approach,
            'product_info': order.product_info,
            'further_info': order.further_info,
            'existing_agents': order.existing_agents,
            'permission_to_approach_contacts': order.permission_to_approach_contacts,
            'delivery_date': order.delivery_date.isoformat(),
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'po_number': order.po_number,
            'discount_value': order.discount_value,
            'vat_status': order.vat_status,
            'vat_number': order.vat_number,
            'vat_verified': order.vat_verified,
            'net_cost': order.net_cost,
            'subtotal_cost': order.subtotal_cost,
            'vat_cost': order.vat_cost,
            'total_cost': order.total_cost,
            'billing_company_name': order.billing_company_name,
            'billing_contact_name': order.billing_contact_name,
            'billing_email': order.billing_email,
            'billing_phone': order.billing_phone,
            'billing_address_1': order.billing_address_1,
            'billing_address_2': order.billing_address_2,
            'billing_address_town': order.billing_address_town,
            'billing_address_county': order.billing_address_county,
            'billing_address_postcode': order.billing_address_postcode,
            'billing_address_country': {
                'id': str(order.billing_address_country.pk),
                'name': order.billing_address_country.name,
            },
            'archived_documents_url_path': order.archived_documents_url_path,
            'paid_on': None,
            'completed_by': None,
            'completed_on': None,
            'cancelled_by': None,
            'cancelled_on': None,
            'cancellation_reason': None,
        }

    def test_not_found(self):
        """Test 404 when getting a non-existing order"""
        url = reverse(
            'api-v3:omis:order:detail',
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'},
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
