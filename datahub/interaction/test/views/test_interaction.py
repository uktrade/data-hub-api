from datetime import date

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import APITestMixin, create_test_user, random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from .test_common import NON_RESTRICTED_CHANGE_PERMISSIONS, NON_RESTRICTED_READ_PERMISSIONS
from ..factories import (
    CompanyInteractionFactory, InvestmentProjectInteractionFactory
)
from ...models import (
    CommunicationChannel, Interaction, InteractionPermission, PolicyArea,
    PolicyIssueType, ServiceDeliveryStatus
)


class TestAddInteraction(APITestMixin):
    """Tests for the add interaction view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_company_interaction(self):
        """Test add new interaction."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
        }
        response = self.api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.interaction,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': None,
            'policy_issue_type': None,
            'communication_channel': {
                'id': str(communication_channel.pk),
                'name': communication_channel.name
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
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_investment_project_interaction(self):
        """Test add new interaction for an investment project."""
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'kind': Interaction.KINDS.interaction,
            'contact': contact.pk,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,

        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_adviser']['id'] == str(adviser.pk)
        assert response_data['investment_project']['id'] == str(project.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208Z'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208Z'

    def test_fails_with_missing_fields(self):
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

    def test_fails_with_missing_interaction_only_fields(self):
        """Test add new interaction without required interaction-only fields."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
        }
        response = self.api_client.post(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'communication_channel': ['This field is required.'],
        }

    def test_fails_with_service_delivery_fields(self):
        """Tests that adding an interaction with an event fails."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'is_event': False,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
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
            'net_company_receipt': '8888.11',
        }
        response = self.api_client.post(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'is_event': ['This field is only valid for service deliveries.'],
            'event': ['This field is only valid for event service deliveries.'],
            'service_delivery_status': ['This field is only valid for service deliveries.'],
            'grant_amount_offered': ['This field is only valid for service deliveries.'],
            'net_company_receipt': ['This field is only valid for service deliveries.'],
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
            'kind': Interaction.KINDS.interaction,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
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

    def test_fails_without_entity(self):
        """Test add new interaction without a contact, company or
        investment project.
        """
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'kind': Interaction.KINDS.interaction,
            'contact': contact.pk,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': AdviserFactory().pk,
            'notes': 'hello',
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
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
            'kind': Interaction.KINDS.interaction,
            'contact': contact.pk,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
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
            'kind': Interaction.KINDS.interaction,
            'contact': contact.pk,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
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
            'kind': Interaction.KINDS.interaction,
            'company': company.pk,
            'contact': contact.pk,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
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


class TestGetInteraction(APITestMixin):
    """Tests for the get interaction view."""

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
            'kind': Interaction.KINDS.interaction,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': None,
            'policy_issue_type': None,
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
            'kind': Interaction.KINDS.interaction,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': None,
            'policy_issue_type': None,
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
            'kind': Interaction.KINDS.interaction,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': None,
            'policy_issue_type': None,
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


class TestUpdateInteraction(APITestMixin):
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
