import pytest
from dateutil.parser import parse as dateutil_parse
from django.utils.timezone import now

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.constants import Country, Sector
from datahub.core.test_utils import APITestMixin

from ..factories import OrderFactory

from ...models import ServiceType


# mark the whole module for db use
pytestmark = pytest.mark.django_db


class TestAddOrderDetails(APITestMixin):
    """Add Order details test case."""

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
    def test_success(self):
        """Test a successful call to create an Order."""
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        country = Country.france.value
        sector = Sector.aerospace_assembly_aircraft.value
        service_type = ServiceType.objects.filter(disabled_on__isnull=True).first()

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {
                    'id': company.pk
                },
                'contact': {
                    'id': contact.pk
                },
                'primary_market': {
                    'id': country.id
                },
                'sector': {
                    'id': sector.id
                },
                'service_types': [
                    {
                        'id': service_type.id
                    },
                ],
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': response.json()['id'],
            'reference': response.json()['reference'],
            'created_on': '2017-04-18T13:00:00',
            'created_by': {
                'id': str(self.user.id),
                'name': self.user.name
            },
            'modified_on': '2017-04-18T13:00:00',
            'modified_by': {
                'id': str(self.user.id),
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
                    'id': str(service_type.id),
                    'name': service_type.name
                }
            ],
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
                'company': {
                    'id': company.pk
                },
                'contact': {
                    'id': contact.pk
                },
                'primary_market': {
                    'id': country.id
                },
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['sector'] is None
        assert response.json()['service_types'] == []

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
                'company': {
                    'id': company.pk
                },
                'contact': {
                    'id': contact.pk
                },
                'primary_market': {
                    'id': country.id
                },
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

    @freeze_time('2017-09-08 11:00:00.000000')
    def test_fails_if_service_type_disabled(self):
        """Test that if a service type specified is disabled, the creation fails."""
        company = CompanyFactory()
        disabled_service_type = ServiceType.objects.filter(disabled_on__lte=now()).first()

        url = reverse('api-v3:omis:order:list')
        response = self.api_client.post(
            url,
            {
                'company': {
                    'id': company.pk
                },
                'contact': {
                    'id': ContactFactory(company=company).pk
                },
                'primary_market': {
                    'id': Country.france.value.id
                },
                'service_types': [
                    {
                        'id': disabled_service_type.id
                    },
                ],
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'service_types': [f'"{disabled_service_type.name}" disabled.']
        }


class TestChangeOrderDetails(APITestMixin):
    """Change Order details test case."""

    @freeze_time('2017-04-18 13:00:00.000000+00:00')
    def test_success(self):
        """Test changing an existing order."""
        order = OrderFactory()
        new_contact = ContactFactory(company=order.company)
        new_sector = Sector.renewable_energy_wind.value
        new_service_type = ServiceType.objects.filter(disabled_on__isnull=True).first()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'contact': {
                    'id': new_contact.id
                },
                'sector': {
                    'id': new_sector.id
                },
                'service_types': [
                    {
                        'id': str(new_service_type.id)
                    }
                ],
            },
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(order.id),
            'reference': order.reference,
            'created_on': '2017-04-18T13:00:00',
            'created_by': {
                'id': str(order.created_by.id),
                'name': order.created_by.name
            },
            'modified_on': '2017-04-18T13:00:00',
            'modified_by': {
                'id': str(self.user.id),
                'name': self.user.name
            },
            'company': {
                'id': str(order.company.id),
                'name': order.company.name
            },
            'contact': {
                'id': str(new_contact.id),
                'name': new_contact.name
            },
            'primary_market': {
                'id': str(order.primary_market.id),
                'name': order.primary_market.name
            },
            'sector': {
                'id': new_sector.id,
                'name': new_sector.name
            },
            'service_types': [
                {
                    'id': str(new_service_type.id),
                    'name': new_service_type.name
                }
            ]
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
                'contact': {
                    'id': other_contact.id
                },
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
                'company': {
                    'id': company.id
                },
                'contact': {
                    'id': contact.id
                },
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
                'primary_market': {
                    'id': Country.greece.value.id
                },
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
                'contact': {
                    'id': '00000000-0000-0000-0000-000000000000'
                },
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contact': [
                'Invalid pk "00000000-0000-0000-0000-000000000000" - object does not exist.'
            ],
        }

    @freeze_time('2017-09-08 11:00:00.000000')
    def test_fails_if_service_type_disabled(self):
        """Test that if a service type specified is disabled, the update fails."""
        order = OrderFactory()
        disabled_service_type = ServiceType.objects.filter(disabled_on__lte=now()).first()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.patch(
            url,
            {
                'service_types': [
                    {
                        'id': disabled_service_type.id
                    },
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
                    {
                        'id': disabled_in_feb.id
                    },
                ]
            },
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['service_types'] == [
            {
                'id': str(disabled_in_feb.id),
                'name': disabled_in_feb.name
            }
        ]


class TestViewOrderDetails(APITestMixin):
    """View order details test case."""

    def test_get(self):
        """Test getting an existing order."""
        order = OrderFactory()

        url = reverse('api-v3:omis:order:detail', kwargs={'pk': order.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(order.id),
            'reference': order.reference,
            'created_on': order.created_on.isoformat(),
            'created_by': {
                'id': str(order.created_by.id),
                'name': order.created_by.name
            },
            'modified_on': order.modified_on.isoformat(),
            'modified_by': {
                'id': str(order.modified_by.id),
                'name': order.modified_by.name
            },
            'company': {
                'id': str(order.company.id),
                'name': order.company.name
            },
            'contact': {
                'id': str(order.contact.id),
                'name': order.contact.name
            },
            'primary_market': {
                'id': str(order.primary_market.id),
                'name': order.primary_market.name
            },
            'sector': {
                'id': str(order.sector.id),
                'name': order.sector.name
            },
            'service_types': [
                {
                    'id': str(service_type.id),
                    'name': service_type.name
                } for service_type in order.service_types.all()
            ]
        }

    def test_not_found(self):
        """Test 404 when getting a non-existing order"""
        url = reverse(
            'api-v3:omis:order:detail',
            kwargs={
                'pk': '00000000-0000-0000-0000-000000000000'
            }
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
