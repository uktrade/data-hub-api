import uuid
import pytest
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import now

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.constants import Country, Sector
from datahub.core.test_utils import APITestMixin
from datahub.omis.market.models import Market

from ..factories import OrderFactory

from ...constants import OrderStatus, VATStatus
from ...models import ServiceType


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestAddOrderDetails(APITestMixin):
    """Add Order details test case."""

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
    def test_success_complete(self):
        """Test a successful call to create an Order with all possible fields."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.france.value
        sector = Sector.aerospace_assembly_aircraft.value
        service_type = ServiceType.objects.filter(disabled_on__isnull=True).first()

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
                'primary_market': {'id': country.id},
                'sector': {'id': sector.id},
                'service_types': [
                    {'id': service_type.pk},
                ],
                'description': 'Description test',
                'contacts_not_to_approach': 'Contacts not to approach details',
                'delivery_date': '2017-04-20',
                'po_number': 'PO 123',
                'vat_status': VATStatus.eu,
                'vat_number': '01234566789',
                'vat_verified': True,
                'billing_contact_name': 'Billing contact name',
                'billing_email': 'billing@example.com',
                'billing_phone': '00112233',
                'billing_address_1': 'Apt 1',
                'billing_address_2': 'London Street',
                'billing_address_town': 'London',
                'billing_address_county': 'London',
                'billing_address_postcode': 'SW1A1AA',
                'billing_address_country': Country.united_kingdom.value.id,
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'reference': response.json()['reference'],
            'status': OrderStatus.draft,
            'created_on': '2017-04-18T13:00:00',
            'created_by': {
                'id': str(self.user.pk),
                'name': self.user.name
            },
            'modified_on': '2017-04-18T13:00:00',
            'modified_by': {
                'id': str(self.user.pk),
                'name': self.user.name
            },
            'company': {
                'id': str(company.pk),
                'name': company.name
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name
            },
            'primary_market': {
                'id': str(country.id),
                'name': country.name
            },
            'sector': {
                'id': sector.id,
                'name': sector.name
            },
            'service_types': [
                {
                    'id': str(service_type.pk),
                    'name': service_type.name
                }
            ],
            'description': 'Description test',
            'contacts_not_to_approach': 'Contacts not to approach details',
            'product_info': '',
            'further_info': '',
            'existing_agents': '',
            'permission_to_approach_contacts': '',
            'delivery_date': '2017-04-20',
            'contact_email': '',
            'contact_phone': '',
            'po_number': 'PO 123',
            'discount_value': 0,
            'vat_status': VATStatus.eu,
            'vat_number': '01234566789',
            'vat_verified': True,
            'net_cost': 0,
            'subtotal_cost': 0,
            'vat_cost': 0,
            'total_cost': 0,
            'billing_contact_name': 'Billing contact name',
            'billing_email': 'billing@example.com',
            'billing_phone': '00112233',
            'billing_address_1': 'Apt 1',
            'billing_address_2': 'London Street',
            'billing_address_town': 'London',
            'billing_address_county': 'London',
            'billing_address_postcode': 'SW1A1AA',
            'billing_address_country': {
                'id': str(Country.united_kingdom.value.id),
                'name': Country.united_kingdom.value.name
            },
            'archived_documents_url_path': '',
            'completed_by': None,
            'completed_on': None,
            'cancelled_by': None,
            'cancelled_on': None,
            'cancellation_reason': None,
        }

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
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
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['sector'] is None
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
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': ['The contact does not work at the given company.'],
        }

    def test_general_validation(self):
        """Test create an Order general validation."""
        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ['This field is required.'],
            'contact': ['This field is required.'],
            'primary_market': ['This field is required.'],
        }

    @freeze_time('2017-10-25 11:00:00.000000')
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
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'service_types': [f'"{disabled_service_type.name}" disabled.']
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
                'primary_market': {'id': disabled_country.pk}
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'primary_market': [f'"{disabled_country.name}" disabled.']
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
                'primary_market': {'id': non_market_country.pk}
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'primary_market': [
                f"The OMIS market for country '{non_market_country}' doesn't exist."
            ]
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
                'further_info': 'lorem ipsum',
                'existing_agents': 'lorem ipsum',
                'permission_to_approach_contacts': 'lorem ipsum',
                'archived_documents_url_path': '/documents/123',
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['product_info'] == ''
        assert response.json()['further_info'] == ''
        assert response.json()['existing_agents'] == ''
        assert response.json()['permission_to_approach_contacts'] == ''
        assert response.json()['archived_documents_url_path'] == ''

    @pytest.mark.parametrize(
        'vat_status',
        (VATStatus.outside_eu, VATStatus.uk)
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
            format='json'
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
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'billing_address_1': ['This field is required.'],
            'billing_address_town': ['This field is required.'],
            'billing_address_postcode': ['This field is required.'],
            'billing_address_country': ['This field is required.'],
        }

    @pytest.mark.parametrize(
        'field,value',
        (
            ('billing_contact_name', 'lorem'),
            ('billing_email', 'billing@example.com'),
            ('billing_phone', '0011'),
        )
    )
    def test_ok_with_non_address_billing_fields_set(self, field, value):
        """
        Test that if a non-address billing field is set, the validation of the
        billing address is not triggered.
        E.g. I can set billing email without billing address.
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
                field: value,
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED


class TestChangeOrderDetails(APITestMixin):
    """Change Order details test case."""

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
    def test_success(self):
        """Test changing an existing order."""
        order = OrderFactory(vat_status=VATStatus.outside_eu)
        new_contact = ContactFactory(company=order.company)
        new_sector = Sector.renewable_energy_wind.value
        new_service_type = ServiceType.objects.filter(disabled_on__isnull=True).first()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'contact': {'id': new_contact.pk},
                'sector': {'id': new_sector.id},
                'service_types': [
                    {'id': str(new_service_type.pk)},
                ],
                'description': 'Updated description',
                'contacts_not_to_approach': 'Updated contacts not to approach',
                'delivery_date': '2017-04-21',
                'po_number': 'NEW PO 321',
                'vat_status': VATStatus.eu,
                'vat_number': 'new vat number',
                'vat_verified': False,
                'billing_contact_name': 'Billing contact name',
                'billing_email': 'billing@example.com',
                'billing_phone': '00112233',
                'billing_address_1': 'Apt 1',
                'billing_address_2': 'London Street',
                'billing_address_town': 'London',
                'billing_address_county': 'London',
                'billing_address_postcode': 'SW1A1AA',
                'billing_address_country': Country.united_kingdom.value.id,
            },
            format='json'
        )

        order.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(order.pk),
            'reference': order.reference,
            'status': OrderStatus.draft,
            'created_on': '2017-04-18T13:00:00',
            'created_by': {
                'id': str(order.created_by.pk),
                'name': order.created_by.name
            },
            'modified_on': '2017-04-18T13:00:00',
            'modified_by': {
                'id': str(self.user.pk),
                'name': self.user.name
            },
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name
            },
            'contact': {
                'id': str(new_contact.pk),
                'name': new_contact.name
            },
            'primary_market': {
                'id': str(order.primary_market.pk),
                'name': order.primary_market.name
            },
            'sector': {
                'id': new_sector.id,
                'name': new_sector.name
            },
            'service_types': [
                {
                    'id': str(new_service_type.pk),
                    'name': new_service_type.name
                }
            ],
            'description': 'Updated description',
            'contacts_not_to_approach': 'Updated contacts not to approach',
            'product_info': order.product_info,
            'further_info': order.further_info,
            'existing_agents': order.existing_agents,
            'permission_to_approach_contacts': order.permission_to_approach_contacts,
            'delivery_date': '2017-04-21',
            'contact_email': order.contact_email,
            'contact_phone': order.contact_phone,
            'po_number': 'NEW PO 321',
            'discount_value': order.discount_value,
            'vat_status': VATStatus.eu,
            'vat_number': 'new vat number',
            'vat_verified': False,
            'net_cost': order.net_cost,
            'subtotal_cost': order.subtotal_cost,
            'vat_cost': order.vat_cost,
            'total_cost': order.total_cost,
            'billing_contact_name': 'Billing contact name',
            'billing_email': 'billing@example.com',
            'billing_phone': '00112233',
            'billing_address_1': 'Apt 1',
            'billing_address_2': 'London Street',
            'billing_address_town': 'London',
            'billing_address_county': 'London',
            'billing_address_postcode': 'SW1A1AA',
            'billing_address_country': {
                'id': str(Country.united_kingdom.value.id),
                'name': Country.united_kingdom.value.name
            },
            'archived_documents_url_path': '',
            'completed_by': None,
            'completed_on': None,
            'cancelled_by': None,
            'cancelled_on': None,
            'cancellation_reason': None,
        }

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
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': ['The contact does not work at the given company.'],
        }

    def test_cannot_change_company(self):
        """Test that company cannot be changed."""
        order = OrderFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'company': {'id': company.pk},
                'contact': {'id': contact.pk},
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'company': ['The company cannot be changed after creation.'],
        }

    def test_cannot_change_primary_market(self):
        """Test that primary market cannot be changed."""
        order = OrderFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'primary_market': {'id': Country.greece.value.id},
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'primary_market': ['The primary market cannot be changed after creation.'],
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
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': [
                'Invalid pk "00000000-0000-0000-0000-000000000000" - object does not exist.'
            ],
        }

    @freeze_time('2017-10-25 11:00:00.000000')
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
                ]
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'service_types': [f'"{disabled_service_type.name}" disabled.']
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

        disabled_in_jan.disabled_on = dateutil_parse('2017-01-10 11:00:00')
        disabled_in_jan.save()

        disabled_in_feb.disabled_on = dateutil_parse('2017-02-01 11:00:00')
        disabled_in_feb.save()

        order = OrderFactory(service_types=[disabled_in_jan])

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'service_types': [
                    {'id': disabled_in_feb.pk},
                ]
            },
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['service_types'] == [
            {
                'id': str(disabled_in_feb.pk),
                'name': disabled_in_feb.name
            }
        ]

    def test_can_save_with_primary_market_disabled(self):
        """
        Test that if the primary market was not disabled at the creation time
        but it became later on, the record can still be saved without any
        validation error.
        """
        market = Market.objects.filter(disabled_on__isnull=True).first()
        country = market.country

        with freeze_time('2017-01-01'):
            order = OrderFactory(primary_market_id=country.pk)

        market.disabled_on = dateutil_parse('2017-02-01')
        market.save()

        with freeze_time('2017-03-01'):
            url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
            response = self.api_client.patch(
                url,
                {
                    'primary_market': country.pk
                },
                format='json'
            )

            assert response.status_code == status.HTTP_200_OK

    def test_cannot_change_readonly_fields(self):
        """Test that if readonly fields are passed in when updating an order, they get ignored."""
        order = OrderFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'status': OrderStatus.complete,
                'product_info': 'Updated product info',
                'further_info': 'Updated further info',
                'existing_agents': 'Updated existing agents',
                'permission_to_approach_contacts': 'Updated permission to approach contacts',
                'contact_email': 'updated-email@email.com',
                'contact_phone': '1234',
                'discount_value': 99999,
                'net_cost': 99999,
                'subtotal_cost': 99999,
                'vat_cost': 99999,
                'total_cost': 99999,
                'archived_documents_url_path': '/documents/123',
                'completed_by': order.created_by.pk,
                'completed_on': now().isoformat(),
                'cancelled_by': order.created_by.pk,
                'cancelled_on': now().isoformat(),
                'cancellation_reason': {
                    'id': uuid.uuid4()
                }
            },
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == OrderStatus.draft
        assert response.json()['product_info'] != 'Updated product info'
        assert response.json()['further_info'] != 'Updated further info'
        assert response.json()['existing_agents'] != 'Updated existing agents'
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
        assert not response.json()['completed_by']
        assert not response.json()['completed_on']
        assert not response.json()['cancelled_by']
        assert not response.json()['cancelled_on']
        assert not response.json()['cancellation_reason']

    @pytest.mark.parametrize(
        'disallowed_status', (
            OrderStatus.quote_awaiting_acceptance,
            OrderStatus.quote_accepted,
            OrderStatus.paid,
            OrderStatus.complete,
            OrderStatus.cancelled,
        )
    )
    def test_409_if_order_not_in_draft(self, disallowed_status):
        """
        Test that if the order is not in one of the allowed statuses, the endpoint
        returns 409.
        """
        order = OrderFactory(status=disallowed_status)

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(url, {}, format='json')
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json() == {
            'detail': (
                'The action cannot be performed '
                f'in the current status {OrderStatus[disallowed_status]}.'
            )
        }

    @pytest.mark.parametrize(
        'vat_status',
        (VATStatus.outside_eu, VATStatus.uk)
    )
    def test_vat_number_and_verified_reset_if_vat_status_not_eu(self, vat_status):
        """
        Test that if vat_number and vat_verified are set but vat_status != 'eu',
        they are set to '' and None as they only make sense if company in 'eu'.
        """
        order = OrderFactory(
            vat_status=VATStatus.eu,
            vat_number='0123456789',
            vat_verified=True
        )

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {'vat_status': vat_status},
            format='json'
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
            billing_address_town=''
        )
        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'billing_address_2': 'London Street',
            },
            format='json'
        )

        order.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'billing_address_1': ['This field is required.'],
            'billing_address_town': ['This field is required.'],
            'billing_address_postcode': ['This field is required.'],
            'billing_address_country': ['This field is required.'],
        }


class TestViewOrderDetails(APITestMixin):
    """View order details test case."""

    def test_get(self):
        """Test getting an existing order."""
        order = OrderFactory(
            archived_documents_url_path='/documents/123'
        )

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(order.pk),
            'reference': order.reference,
            'status': OrderStatus.draft,
            'created_on': order.created_on.isoformat(),
            'created_by': {
                'id': str(order.created_by.pk),
                'name': order.created_by.name
            },
            'modified_on': order.modified_on.isoformat(),
            'modified_by': {
                'id': str(order.modified_by.pk),
                'name': order.modified_by.name
            },
            'company': {
                'id': str(order.company.pk),
                'name': order.company.name
            },
            'contact': {
                'id': str(order.contact.pk),
                'name': order.contact.name
            },
            'primary_market': {
                'id': str(order.primary_market.pk),
                'name': order.primary_market.name
            },
            'sector': {
                'id': str(order.sector.id),
                'name': order.sector.name
            },
            'service_types': [
                {
                    'id': str(service_type.pk),
                    'name': service_type.name
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
                'name': order.billing_address_country.name
            },
            'archived_documents_url_path': order.archived_documents_url_path,
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
            kwargs={'pk': '00000000-0000-0000-0000-000000000000'}
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
