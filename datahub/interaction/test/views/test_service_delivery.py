from datetime import date

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import APITestMixin, random_obj_for_model
from datahub.event.test.factories import EventFactory
from ..factories import (
    EventServiceDeliveryFactory, ServiceDeliveryFactory
)
from ...models import (
    CommunicationChannel, Interaction, PolicyArea, PolicyIssueType, ServiceDeliveryStatus
)


class TestAddServiceDelivery(APITestMixin):
    """Tests for the add service delivery view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_event_service_delivery(self):
        """Test adding a new event service delivery."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        event = EventFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'is_event': True,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'event': event.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.service_delivery,
            'is_event': True,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'communication_channel': None,
            'policy_area': None,
            'policy_issue_type': None,
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_adviser': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name
            },
            'notes': 'hello',
            'company': {
                'id': str(company.pk),
                'name': company.name
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name
            },
            'event': {
                'id': str(event.pk),
                'name': event.name,
            },
            'service': {
                'id': str(Service.trade_enquiry.value.id),
                'name': Service.trade_enquiry.value.name,
            },
            'dit_team': {
                'id': str(Team.healthcare_uk.value.id),
                'name': Team.healthcare_uk.value.name,
            },
            'investment_project': None,
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'modified_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z'
        }

    def test_adding_event_service_delivery_fails_with_missing_event(self):
        """Test adding a new event service delivery without specifying an event."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'is_event': True,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'event': None,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'event': ['This field is required.']
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_non_event_service_delivery(self):
        """
        Test adding a new non-event service delivery with blank status and grant amount
        offered.
        """
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'is_event': False,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'is_event': False,
            'kind': Interaction.KINDS.service_delivery,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'communication_channel': None,
            'policy_area': None,
            'policy_issue_type': None,
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_adviser': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name
            },
            'notes': 'hello',
            'company': {
                'id': str(company.pk),
                'name': company.name
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name
            },
            'event': None,
            'service': {
                'id': str(Service.trade_enquiry.value.id),
                'name': Service.trade_enquiry.value.name,
            },
            'dit_team': {
                'id': str(Team.healthcare_uk.value.id),
                'name': Team.healthcare_uk.value.name,
            },
            'investment_project': None,
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'modified_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z'
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_non_event_service_delivery_extended(self):
        """Test adding a new non-event service delivery with status and grant amount offered."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        service_delivery_status = random_obj_for_model(ServiceDeliveryStatus)
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'service_delivery_status': service_delivery_status.pk,
            'grant_amount_offered': '9999.99',
            'net_company_receipt': '8888.99',
            'is_event': False,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'is_event': False,
            'kind': Interaction.KINDS.service_delivery,
            'service_delivery_status': {
                'id': str(service_delivery_status.pk),
                'name': service_delivery_status.name,
            },
            'grant_amount_offered': '9999.99',
            'net_company_receipt': '8888.99',
            'communication_channel': None,
            'policy_area': None,
            'policy_issue_type': None,
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_adviser': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name
            },
            'notes': 'hello',
            'company': {
                'id': str(company.pk),
                'name': company.name
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name
            },
            'event': None,
            'service': {
                'id': str(Service.trade_enquiry.value.id),
                'name': Service.trade_enquiry.value.name,
            },
            'dit_team': {
                'id': str(Team.healthcare_uk.value.id),
                'name': Team.healthcare_uk.value.name,
            },
            'investment_project': None,
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'modified_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z'
        }

    def test_adding_non_event_service_delivery_with_event_fails(self):
        """Test add new non-event service delivery with an event specified."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        event = EventFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'is_event': False,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'event': event.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'event': ['This field is only valid for event service deliveries.']
        }

    def test_fails_with_policy_feedback_fields(self):
        """Tests that adding a service delivery with a policy area & issue_type fails."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        policy_area = random_obj_for_model(PolicyArea)
        policy_issue_type = random_obj_for_model(PolicyIssueType)

        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'is_event': True,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
            'event': EventFactory().pk,
            'policy_area': policy_area.pk,
            'policy_issue_type': policy_issue_type.pk
        }
        response = self.api_client.post(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'policy_area': ['This field is only valid for policy feedback.'],
            'policy_issue_type': ['This field is only valid for policy feedback.']
        }

    def test_fails_with_interaction_fields(self):
        """Tests that adding a service delivery with a communication channel fails."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'is_event': True,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
            'event': EventFactory().pk
        }
        response = self.api_client.post(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'communication_channel': ['This field is only valid for interactions.'],
        }


class TestUpdateServiceDelivery(APITestMixin):
    """Tests for the update interaction view."""

    def test_change_non_event_service_delivery_to_event(self):
        """Test making a non-event service delivery an event service delivery."""
        service_delivery = ServiceDeliveryFactory()
        event = EventFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': service_delivery.pk})
        response = self.api_client.patch(url, {
            'is_event': True,
            'event': event.pk
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['is_event'] is True
        assert response_data['event'] == {
            'id': str(event.pk),
            'name': event.name,
        }

    def test_change_event_service_delivery_to_non_event(self):
        """Test making an event service delivery a non-event service delivery."""
        service_delivery = EventServiceDeliveryFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': service_delivery.pk})
        response = self.api_client.patch(url, {
            'is_event': False,
            'event': None
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['is_event'] is False
        assert response_data['event'] is None

    def test_fails_with_negative_grant_amount(self):
        """Test validation when an a negative grant amount offered is entered."""
        interaction = ServiceDeliveryFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'grant_amount_offered': '-100.00',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['grant_amount_offered'] == [
            'Ensure this value is greater than or equal to 0.'
        ]

    def test_fails_with_negative_net_company_receipt(self):
        """Test validation when an a negative net company receipt is entered."""
        interaction = ServiceDeliveryFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'net_company_receipt': '-100.00',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['net_company_receipt'] == [
            'Ensure this value is greater than or equal to 0.'
        ]
