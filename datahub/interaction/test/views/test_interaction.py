from datetime import date
from functools import partial
from itertools import chain

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import APITestMixin, create_test_user, random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
    InteractionPermission,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    CompanyInteractionFactoryWithPolicyFeedback,
    InvestmentProjectInteractionFactory,
)
from datahub.interaction.test.views.utils import resolve_data
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory


NON_RESTRICTED_VIEW_PERMISSIONS = (
    (
        InteractionPermission.view_all,
    ),
    (
        InteractionPermission.view_all,
        InteractionPermission.view_associated_investmentproject,
    ),
)


NON_RESTRICTED_ADD_PERMISSIONS = (
    (
        InteractionPermission.add_all,
    ),
    (
        InteractionPermission.add_all,
        InteractionPermission.add_associated_investmentproject,
    ),
)


NON_RESTRICTED_CHANGE_PERMISSIONS = (
    (
        InteractionPermission.change_all,
    ),
    (
        InteractionPermission.change_all,
        InteractionPermission.change_associated_investmentproject,
    ),
)


class TestAddInteraction(APITestMixin):
    """Tests for the add interaction view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'extra_data',
        (
            # company interaction
            {
                'was_policy_feedback_provided': False,
            },
            # company interaction with blank notes
            {
                'was_policy_feedback_provided': False,
                'notes': '',
            },
            # company interaction with notes
            {
                'was_policy_feedback_provided': False,
                'notes': 'hello',
            },
            # investment project interaction
            {
                'was_policy_feedback_provided': False,
                'investment_project': InvestmentProjectFactory,
                'notes': 'hello',
            },
            # company interaction without was_policy_feedback_provided explicitly specified
            # (for backwards compatibility)
            {
            },
            # company interaction with policy feedback
            {
                'was_policy_feedback_provided': True,
                'policy_areas': [
                    partial(random_obj_for_model, PolicyArea),
                ],
                'policy_feedback_notes': 'Policy feedback notes',
                'policy_issue_types': [partial(random_obj_for_model, PolicyIssueType)],
            },
        ),
    )
    def test_add(self, extra_data, permissions):
        """Test add a new interaction."""
        adviser = create_test_user(permission_codenames=permissions)
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
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,

            **resolve_data(extra_data),
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.interaction,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': request_data.get('policy_areas', []),
            'policy_feedback_notes': request_data.get('policy_feedback_notes', ''),
            'policy_issue_type': None,
            'policy_issue_types':
                request_data.get('policy_issue_types', []),
            'was_policy_feedback_provided':
                request_data.get('was_policy_feedback_provided', False),
            'communication_channel': {
                'id': str(communication_channel.pk),
                'name': communication_channel.name,
            },
            'subject': 'whatever',
            'date': '2017-04-18',
            'dit_adviser': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'notes': request_data.get('notes', ''),
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'contact': {
                'id': str(contact.pk),
                'name': contact.name,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'job_title': contact.job_title,
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
            'investment_project': request_data.get('investment_project'),
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'modified_by': {
                'id': str(adviser.pk),
                'first_name': adviser.first_name,
                'last_name': adviser.last_name,
                'name': adviser.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    @pytest.mark.parametrize(
        'data,errors',
        (
            # required fields
            (
                {
                    'kind': Interaction.KINDS.interaction,
                },
                {
                    'date': ['This field is required.'],
                    'subject': ['This field is required.'],
                    'company': ['This field is required.'],
                    'contact': ['This field is required.'],
                    'dit_adviser': ['This field is required.'],
                    'service': ['This field is required.'],
                    'dit_team': ['This field is required.'],
                },
            ),

            # interaction fields required
            (
                {
                    'kind': Interaction.KINDS.interaction,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                },
                {
                    'communication_channel': ['This field is required.'],
                },
            ),

            # policy feedback fields required when policy feedback provided
            (
                {
                    'kind': Interaction.KINDS.interaction,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),

                    'was_policy_feedback_provided': True,
                },
                {
                    'policy_areas': ['This field is required.'],
                    'policy_feedback_notes': ['This field is required.'],
                    'policy_issue_types': ['This field is required.'],
                },
            ),

            # policy feedback fields cannot be blank when policy feedback provided
            (
                {
                    'kind': Interaction.KINDS.interaction,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),

                    'was_policy_feedback_provided': True,
                    'policy_areas': [],
                    'policy_feedback_notes': '',
                    'policy_issue_types': [],
                },
                {
                    'policy_areas': ['This field is required.'],
                    'policy_feedback_notes': ['This field is required.'],
                    'policy_issue_types': ['This field is required.'],
                },
            ),

            # fields not allowed
            (
                {
                    'kind': Interaction.KINDS.interaction,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),

                    # fields not allowed
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    'policy_areas': [partial(random_obj_for_model, PolicyArea)],
                    'policy_feedback_notes': 'Policy feedback notes.',
                    'policy_issue_types': [partial(random_obj_for_model, PolicyIssueType)],
                },
                {
                    'is_event': ['This field is only valid for service deliveries.'],
                    'event': ['This field is only valid for service deliveries.'],
                    'service_delivery_status': [
                        'This field is only valid for service deliveries.',
                    ],
                    'grant_amount_offered': ['This field is only valid for service deliveries.'],
                    'net_company_receipt': ['This field is only valid for service deliveries.'],
                    'policy_areas': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'policy_feedback_notes': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'policy_issue_types': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                },
            ),

            # fields where None is not allowed
            (
                {
                    'kind': Interaction.KINDS.interaction,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),

                    # fields where None is not allowed
                    'was_policy_feedback_provided': None,
                    'policy_feedback_notes': None,
                },
                {
                    'was_policy_feedback_provided': ['This field may not be null.'],
                    'policy_feedback_notes': ['This field may not be null.'],
                },
            ),
        ),
    )
    def test_validation(self, data, errors):
        """Test validation errors."""
        data = resolve_data(data)
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_restricted_user_can_add_associated_investment_project_interaction(self):
        """
        Test that a restricted user can add an interaction for an associated investment project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.add_associated_investmentproject],
            dit_team=project_creator.dit_team,  # same dit team as the project creator
        )
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(
            url,
            data={
                'kind': Interaction.KINDS.interaction,
                'company': company.pk,
                'contact': contact.pk,
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_adviser': requester.pk,
                'notes': 'hello',
                'investment_project': project.pk,
                'service': Service.trade_enquiry.value.id,
                'dit_team': Team.healthcare_uk.value.id,
            },
        )

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
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.add_associated_investmentproject],
            dit_team=TeamFactory(),  # different dit team from the project creator
        )
        url = reverse('api-v3:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(
            url,
            data={
                'kind': Interaction.KINDS.interaction,
                'company': CompanyFactory().pk,
                'contact': ContactFactory().pk,
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_adviser': requester.pk,
                'notes': 'hello',
                'investment_project': project.pk,
                'service': Service.trade_enquiry.value.id,
                'dit_team': Team.healthcare_uk.value.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'investment_project': [
                "You don't have permission to add an interaction for this "
                'investment project.',
            ],
        }

    def test_restricted_user_cannot_add_company_interaction(self):
        """Test that a restricted user cannot add a company interaction."""
        requester = create_test_user(
            permission_codenames=[InteractionPermission.add_associated_investmentproject],
        )
        url = reverse('api-v3:interaction:collection')
        api_client = self.create_api_client(user=requester)
        response = api_client.post(
            url,
            data={
                'kind': Interaction.KINDS.interaction,
                'company': CompanyFactory().pk,
                'contact': ContactFactory().pk,
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_adviser': requester.pk,
                'notes': 'hello',
                'service': Service.trade_enquiry.value.id,
                'dit_team': Team.healthcare_uk.value.id,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'investment_project': ['This field is required.'],
        }


class TestGetInteraction(APITestMixin):
    """Tests for the get interaction view."""

    @pytest.mark.parametrize(
        'factory',
        (
            CompanyInteractionFactory,
            CompanyInteractionFactoryWithPolicyFeedback,
            InvestmentProjectInteractionFactory,
        ),
    )
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_non_restricted_user_can_get_interaction(self, permissions, factory):
        """Test that a non-restricted user can get various types of interaction."""
        requester = create_test_user(permission_codenames=permissions)
        interaction = factory()
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
            'policy_areas': [
                {
                    'id': str(policy_area.pk),
                    'name': policy_area.name,
                } for policy_area in interaction.policy_areas.all()
            ],
            'policy_feedback_notes': interaction.policy_feedback_notes,
            'policy_issue_type': None,
            'policy_issue_types': [
                {
                    'id': str(policy_issue_type.pk),
                    'name': policy_issue_type.name,
                } for policy_issue_type in interaction.policy_issue_types.all()
            ],
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'last_name': interaction.dit_adviser.last_name,
                'name': interaction.dit_adviser.name,
            },
            'notes': interaction.notes,
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            },
            'contact': {
                'id': str(interaction.contact.pk),
                'name': interaction.contact.name,
                'first_name': interaction.contact.first_name,
                'last_name': interaction.contact.last_name,
                'job_title': interaction.contact.job_title,
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
            } if interaction.investment_project else None,
            'archived_documents_url_path': interaction.archived_documents_url_path,
            'created_by': {
                'id': str(interaction.created_by.pk),
                'first_name': interaction.created_by.first_name,
                'last_name': interaction.created_by.last_name,
                'name': interaction.created_by.name,
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_restricted_user_can_get_associated_investment_project_interaction(self):
        """Test that a restricted user can get an associated investment project interaction."""
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        interaction = InvestmentProjectInteractionFactory(investment_project=project)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.view_associated_investmentproject],
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
            'policy_areas': [],
            'policy_feedback_notes': '',
            'policy_issue_type': None,
            'policy_issue_types': [],
            'was_policy_feedback_provided': False,
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name,
            },
            'subject': interaction.subject,
            'date': interaction.date.date().isoformat(),
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'last_name': interaction.dit_adviser.last_name,
                'name': interaction.dit_adviser.name,
            },
            'notes': interaction.notes,
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            },
            'contact': {
                'id': str(interaction.contact.pk),
                'name': interaction.contact.name,
                'first_name': interaction.contact.first_name,
                'last_name': interaction.contact.last_name,
                'job_title': interaction.contact.job_title,
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
                'name': interaction.created_by.name,
            },
            'modified_by': {
                'id': str(interaction.modified_by.pk),
                'first_name': interaction.modified_by.first_name,
                'last_name': interaction.modified_by.last_name,
                'name': interaction.modified_by.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    def test_restricted_user_cannot_get_non_associated_investment_project_interaction(self):
        """
        Test that a restricted user cannot get a non-associated investment project
        interaction.
        """
        interaction = InvestmentProjectInteractionFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.view_associated_investmentproject],
            dit_team=TeamFactory(),
        )
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_cannot_get_company_interaction(self):
        """Test that a restricted user cannot get a company interaction."""
        interaction = CompanyInteractionFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.view_associated_investmentproject],
            dit_team=TeamFactory(),
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
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_restricted_user_cannot_update_company_interaction(self):
        """Test that a restricted user cannot update a company interaction."""
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject],
        )
        interaction = CompanyInteractionFactory(subject='I am a subject')

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_cannot_update_non_associated_investment_project_interaction(self):
        """
        Test that a restricted user cannot update a non-associated investment project interaction.
        """
        interaction = InvestmentProjectInteractionFactory(
            subject='I am a subject',
        )
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject],
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_restricted_user_can_update_associated_investment_project_interaction(self):
        """
        Test that a restricted user can update an interaction for an associated investment project.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        interaction = CompanyInteractionFactory(
            subject='I am a subject',
            investment_project=project,
        )
        requester = create_test_user(
            permission_codenames=[
                InteractionPermission.change_associated_investmentproject,
            ],
            dit_team=project_creator.dit_team,
        )

        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'subject': 'I am another subject',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'


class TestListInteractions(APITestMixin):
    """Tests for the list interactions view."""

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    def test_non_restricted_user_can_only_list_relevant_interactions(self, permissions):
        """Test that a non-restricted user can list all interactions"""
        requester = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=requester)

        project = InvestmentProjectFactory()
        company = CompanyFactory()
        company_interactions = CompanyInteractionFactory.create_batch(3, company=company)
        project_interactions = CompanyInteractionFactory.create_batch(
            3, investment_project=project,
        )

        url = reverse('api-v3:interaction:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 6
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in chain(project_interactions, company_interactions)}
        assert actual_ids == expected_ids

    def test_restricted_user_can_only_list_associated_interactions(self):
        """
        Test that a restricted user can only list interactions for associated investment
        projects.
        """
        creator = AdviserFactory()
        requester = create_test_user(
            permission_codenames=[InteractionPermission.view_associated_investmentproject],
            dit_team=creator.dit_team,
        )
        api_client = self.create_api_client(user=requester)

        company = CompanyFactory()
        non_associated_project = InvestmentProjectFactory()
        associated_project = InvestmentProjectFactory(created_by=creator)

        CompanyInteractionFactory.create_batch(3, company=company)
        CompanyInteractionFactory.create_batch(
            3, investment_project=non_associated_project,
        )
        associated_project_interactions = CompanyInteractionFactory.create_batch(
            2, investment_project=associated_project,
        )

        url = reverse('api-v3:interaction:collection')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in associated_project_interactions}
        assert actual_ids == expected_ids
