from datetime import date
from itertools import chain

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import APITestMixin, create_test_user, random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.interaction.constants import CommunicationChannel
from datahub.interaction.models import InteractionPermission, ServiceDeliveryStatus

from datahub.interaction.test.factories import (
    CompanyInteractionFactory, EventServiceDeliveryFactory, InvestmentProjectInteractionFactory,
    ServiceDeliveryFactory,
)
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory


NON_RESTRICTED_READ_PERMISSIONS = (
    (
        InteractionPermission.read_all,
    ),
    (
        InteractionPermission.read_all,
        InteractionPermission.read_associated_investmentproject,
    )
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        InteractionPermission.change_all,
    ),
    (
        InteractionPermission.change_all,
        InteractionPermission.change_associated_investmentproject,
    )
)


class TestGetInteractionView(APITestMixin):
    """Tests for the get interaction view."""

    def test_interaction_no_permissions(self):
        """Should return 403"""
        interaction = CompanyInteractionFactory()
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_non_restricted_user_can_get_company_interaction(self, permissions):
        """Test that a non-restricted user can get a company interaction."""
        requester = create_test_user(permission_codenames=permissions)
        interaction = CompanyInteractionFactory()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': 'interaction',
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'last_name': interaction.dit_adviser.last_name,
                'name': interaction.dit_adviser.name
            },
            'notes': interaction.notes,
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name
            },
            'contact': {
                'id': str(interaction.contact.pk),
                'name': interaction.contact.name
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
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'created_by': {
                'id': str(interaction.created_by.pk),
                'first_name': interaction.created_by.first_name,
                'last_name': interaction.created_by.last_name,
                'name': interaction.created_by.name
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z'
        }

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_non_restricted_user_can_get_investment_project_interaction(self, permissions):
        """Test that a non-restricted user can get an investment project interaction."""
        requester = create_test_user(permission_codenames=permissions)
        interaction = InvestmentProjectInteractionFactory()
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': 'interaction',
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'last_name': interaction.dit_adviser.last_name,
                'name': interaction.dit_adviser.name
            },
            'notes': interaction.notes,
            'company': None,
            'contact': {
                'id': str(interaction.contact.pk),
                'name': interaction.contact.name
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
            'investment_project': {
                'id': str(interaction.investment_project.pk),
                'name': interaction.investment_project.name,
                'project_code': interaction.investment_project.project_code,
            },
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'created_by': {
                'id': str(interaction.created_by.pk),
                'first_name': interaction.created_by.first_name,
                'last_name': interaction.created_by.last_name,
                'name': interaction.created_by.name
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z'
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_restricted_user_can_get_associated_investment_project_interaction(self):
        """Test that a restricted user can get an associated investment project interaction."""
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        interaction = InvestmentProjectInteractionFactory(investment_project=project)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.read_associated_investmentproject],
            dit_team=project_creator.dit_team,
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': 'interaction',
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'last_name': interaction.dit_adviser.last_name,
                'name': interaction.dit_adviser.name
            },
            'notes': interaction.notes,
            'company': None,
            'contact': {
                'id': str(interaction.contact.pk),
                'name': interaction.contact.name
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
            'investment_project': {
                'id': str(interaction.investment_project.pk),
                'name': interaction.investment_project.name,
                'project_code': interaction.investment_project.project_code,
            },
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'created_by': {
                'id': str(interaction.created_by.pk),
                'first_name': interaction.created_by.first_name,
                'last_name': interaction.created_by.last_name,
                'name': interaction.created_by.name
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z'
        }

    def test_restricted_user_cannot_get_non_associated_investment_project_interaction(self):
        """
        Test that a restricted user cannot get a non-associated investment project
        interaction.
        """
        interaction = InvestmentProjectInteractionFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.read_associated_investmentproject],
            dit_team=TeamFactory()
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_cannot_get_company_interaction(self):
        """Test that a restricted user cannot get a company interaction."""
        interaction = CompanyInteractionFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.read_associated_investmentproject],
            dit_team=TeamFactory()
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddInteractionView(APITestMixin):
    """Tests for the add interaction view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_interaction(self):
        """Test add new interaction."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'interaction',
            'communication_channel': CommunicationChannel.face_to_face.value.id,
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
            'kind': 'interaction',
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'communication_channel': {
                'id': CommunicationChannel.face_to_face.value.id,
                'name': CommunicationChannel.face_to_face.value.name
            },
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
    def test_add_event_service_delivery(self):
        """Test adding a new event service delivery."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        event = EventFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'service_delivery',
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
            'kind': 'service_delivery',
            'is_event': True,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'communication_channel': None,
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

    def test_add_event_service_delivery_missing_event(self):
        """Test adding a new event service delivery without specifying an event."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'service_delivery',
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
            'kind': 'service_delivery',
            'service_delivery_status': None,
            'grant_amount_offered': None,
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
            'kind': 'service_delivery',
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'communication_channel': None,
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
            'kind': 'service_delivery',
            'service_delivery_status': service_delivery_status.pk,
            'grant_amount_offered': '9999.99',
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
            'kind': 'service_delivery',
            'service_delivery_status': {
                'id': str(service_delivery_status.pk),
                'name': service_delivery_status.name,
            },
            'grant_amount_offered': '9999.99',
            'communication_channel': None,
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

    def test_add_non_event_service_delivery_with_event(self):
        """Test add new non-event service delivery with an event specified."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        event = EventFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'service_delivery',
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

    def test_add_interaction_project_missing_fields(self):
        """Test validation of missing fields."""
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'contact': ['This field is required.'],
            'date': ['This field is required.'],
            'dit_adviser': ['This field is required.'],
            'dit_team': ['This field is required.'],
            'kind': ['This field is required.'],
            'notes': ['This field is required.'],
            'service': ['This field is required.'],
            'subject': ['This field is required.'],
        }

    def test_add_interaction_missing_interaction_only_fields(self):
        """Test add new interaction without required interaction-only fields."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'interaction',
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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'communication_channel': ['This field is required.'],
        }

    def test_add_interaction_with_service_delivery_fields(self):
        """Tests that adding an interaction with an event fails."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'interaction',
            'is_event': False,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
            'event': EventFactory().pk,
            'service_delivery_status': random_obj_for_model(ServiceDeliveryStatus).pk,
            'grant_amount_offered': '1111.11',
        }
        response = self.api_client.post(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'is_event': ['This field is only valid for service deliveries.'],
            'event': ['This field is only valid for event service deliveries.'],
            'service_delivery_status': ['This field is only valid for service deliveries.'],
            'grant_amount_offered': ['This field is only valid for service deliveries.'],
        }

    def test_add_service_delivery_with_interaction_fields(self):
        """Tests that adding a service delivery with a communication channel fails."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': 'service_delivery',
            'is_event': True,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
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

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_interaction_project(self):
        """Test add new interaction for an investment project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'kind': 'interaction',
            'contact': contact.pk,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_adviser']['id'] == str(adviser.pk)
        assert response_data['investment_project']['id'] == str(project.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208Z'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208Z'

    def test_add_interaction_no_entity(self):
        """Test add new interaction without a contact, company or
        investment project.
        """
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'kind': 'interaction',
            'contact': contact.pk,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': AdviserFactory().pk,
            'notes': 'hello',
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'non_field_errors': [
                'One or more of company, investment_project must be provided.'
            ]
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_restricted_user_can_add_associated_investment_project_interaction(self):
        """
        Test that a restricted user can add an interaction for an associated investment project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.add_associated_investmentproject]
        )
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'kind': 'interaction',
            'contact': contact.pk,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': requester.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_adviser']['id'] == str(requester.pk)
        assert response_data['investment_project']['id'] == str(project.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208Z'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208Z'

    def test_restricted_user_cannot_add_non_associated_investment_project_interaction(self):
        """
        Test that a restricted user cannot add an interaction for a non-associated investment
        project.
        """
        project = InvestmentProjectFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.add_associated_investmentproject]
        )
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(url, {
            'kind': 'interaction',
            'contact': contact.pk,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': requester.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'investment_project': ["You don't have permission to add an interaction for this "
                                   'investment project.']
        }

    def test_restricted_user_cannot_add_company_interaction(self):
        """Test that a restricted user cannot add a company interaction."""
        requester = create_test_user(
            permission_codenames=[InteractionPermission.add_associated_investmentproject]
        )
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(url, {
            'kind': 'interaction',
            'company': company.pk,
            'contact': contact.pk,
            'communication_channel': CommunicationChannel.face_to_face.value.id,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': requester.pk,
            'notes': 'hello',
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'investment_project': ['This field is required.']
        }


class TestUpdateInteractionView(APITestMixin):
    """Tests for the update interaction view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_CHANGE_PERMISSIONS)
    def test_non_restricted_user_can_update_interaction(self, permissions):
        """Test that a non-restricted user can update an interaction."""
        requester = create_test_user(permission_codenames=permissions)
        interaction = CompanyInteractionFactory(subject='I am a subject')

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(url, {
            'subject': 'I am another subject',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_restricted_user_cannot_update_company_interaction(self):
        """Test that a restricted user cannot update a company interaction."""
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject]
        )
        interaction = CompanyInteractionFactory(subject='I am a subject')

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(url, {
            'subject': 'I am another subject',
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_cannot_update_non_associated_investment_project_interaction(self):
        """
        Test that a restricted user cannot update a non-associated investment project interaction.
        """
        interaction = InvestmentProjectInteractionFactory(
            subject='I am a subject',
        )
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject]
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(url, {
            'subject': 'I am another subject',
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_update_associated_investment_project_interaction(self):
        """
        Test that a restricted user can update an interaction for an associated investment project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        interaction = CompanyInteractionFactory(
            subject='I am a subject',
            investment_project=project
        )
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.change_associated_investmentproject
            ],
            dit_team=project_creator.dit_team
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(url, {
            'subject': 'I am another subject',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_update_read_only_fields(self):
        """Test updating read-only fields."""
        interaction = CompanyInteractionFactory(
            archived_documents_url_path='old_path',
        )

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, format='json', data={
            'archived_documents_url_path': 'new_path'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived_documents_url_path'] == 'old_path'

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

    def test_date_validation(self):
        """Test validation when an invalid date is provided."""
        interaction = CompanyInteractionFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'date': 'abcd-de-fe',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['date'] == [
            'Datetime has wrong format. Use one of these formats instead: YYYY-MM-DD.'
        ]

    def test_negative_grant_amount_is_rejected(self):
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


class TestListInteractionsView(APITestMixin):
    """Tests for the list interactions view."""

    def test_list_filtered_company(self):
        """List of interactions filtered by company"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        CompanyInteractionFactory.create_batch(3, company=company1)
        interactions = CompanyInteractionFactory.create_batch(2, company=company2)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {'company_id': company2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_list_filtered_contact(self):
        """List of interactions filtered by contact"""
        contact1 = ContactFactory()
        contact2 = ContactFactory()

        CompanyInteractionFactory.create_batch(3, contact=contact1)
        interactions = CompanyInteractionFactory.create_batch(2, contact=contact2)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {'contact_id': contact2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_list_filtered_investment_project(self):
        """List of interactions filtered by investment project"""
        contact = ContactFactory()
        project = InvestmentProjectFactory()
        company = CompanyFactory()

        CompanyInteractionFactory.create_batch(3, contact=contact)
        CompanyInteractionFactory.create_batch(3, company=company)
        project_interactions = CompanyInteractionFactory.create_batch(
            2, investment_project=project
        )

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {
            'investment_project_id': project.id
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in project_interactions}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_READ_PERMISSIONS)
    def test_non_restricted_user_can_only_list_relevant_interactions(self, permissions):
        """Test that a non-restricted user can list all interactions"""
        requester = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=requester)

        project = InvestmentProjectFactory()
        company = CompanyFactory()
        company_interactions = CompanyInteractionFactory.create_batch(3, company=company)
        project_interactions = CompanyInteractionFactory.create_batch(
            3, investment_project=project
        )

        url = reverse('api-v3:interaction:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 6
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in chain(project_interactions, company_interactions)}
        assert actual_ids == expected_ids

    def test_restricted_user_can_only_associated_interactions(self):
        """
        Test that a restricted user can only list interactions for associated investment
        projects.
        """
        creator = AdviserFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.read_associated_investmentproject],
            dit_team=creator.dit_team
        )
        api_client = self.create_api_client(user=requester)

        company = CompanyFactory()
        non_associated_project = InvestmentProjectFactory()
        associated_project = InvestmentProjectFactory(created_by=creator)

        CompanyInteractionFactory.create_batch(3, company=company)
        CompanyInteractionFactory.create_batch(
            3, investment_project=non_associated_project
        )
        associated_project_interactions = CompanyInteractionFactory.create_batch(
            2, investment_project=associated_project
        )

        url = reverse('api-v3:interaction:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in associated_project_interactions}
        assert actual_ids == expected_ids
