from datetime import date
from functools import partial
from operator import attrgetter, itemgetter
from unittest.mock import ANY

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import (
    APITestMixin, format_date_or_datetime, random_obj_for_model
)
from datahub.event.test.factories import EventFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from .utils import (
    create_add_policy_feedback_user,
    create_change_policy_feedback_user,
    create_interaction_user_without_policy_feedback,
    create_read_policy_feedback_user,
    create_restricted_investment_project_user,
    resolve_data,
)
from ..factories import PolicyFeedbackFactory
from ...models import (
    CommunicationChannel,
    Interaction,
    PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)


class TestAddPolicyFeedback(APITestMixin):
    """Tests for the add policy feedback view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add(self):
        """Test add new policy feedback interaction."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        policy_areas = sorted(PolicyArea.objects.order_by('?')[:2], key=attrgetter('pk'))
        policy_issue_type = random_obj_for_model(PolicyIssueType)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.policy_feedback,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
            'policy_areas': [policy_area.pk for policy_area in policy_areas],
            'policy_issue_type': policy_issue_type.pk
        }

        user = create_add_policy_feedback_user()
        api_client = self.create_api_client(user=user)
        response = api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        response_data['policy_areas'] = sorted(response_data['policy_areas'], key=itemgetter('id'))
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.policy_feedback,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': {
                'id': ANY,
                'name': ANY,
            },
            'policy_areas': [{
                'id': str(policy_area.pk),
                'name': policy_area.name,
            } for policy_area in policy_areas],
            'policy_issue_type': {
                'id': str(policy_issue_type.pk),
                'name': policy_issue_type.name,
            },
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
            'investment_project': None,
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(user.pk),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': user.name
            },
            'modified_by': {
                'id': str(user.pk),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': user.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }
        assert any(
            response_data['policy_area'] == {
                'id': str(policy_area.pk),
                'name': policy_area.name,
            } for policy_area in policy_areas
        )

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add_using_legacy_policy_area_field(self):
        """
        Test adding a new policy feedback interaction using the legacy policy_area field.

        This is a separate test from test_add so that this test can be easily removed when
        policy_area is removed.
        """
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        policy_area = random_obj_for_model(PolicyArea)
        policy_issue_type = random_obj_for_model(PolicyIssueType)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.policy_feedback,
            'communication_channel': communication_channel.pk,
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

        user = create_add_policy_feedback_user()
        api_client = self.create_api_client(user=user)
        response = api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.policy_feedback,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': {
                'id': str(policy_area.pk),
                'name': policy_area.name,
            },
            'policy_areas': [{
                'id': str(policy_area.pk),
                'name': policy_area.name,
            }],
            'policy_issue_type': {
                'id': str(policy_issue_type.pk),
                'name': policy_issue_type.name,
            },
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
            'investment_project': None,
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(user.pk),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': user.name
            },
            'modified_by': {
                'id': str(user.pk),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': user.name
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
                    'kind': Interaction.KINDS.policy_feedback,
                },
                {
                    'date': ['This field is required.'],
                    'subject': ['This field is required.'],
                    'notes': ['This field is required.'],
                    'company': ['This field is required.'],
                    'contact': ['This field is required.'],
                    'dit_adviser': ['This field is required.'],
                    'service': ['This field is required.'],
                    'dit_team': ['This field is required.'],
                }
            ),

            # policy fields required
            (
                {
                    'kind': Interaction.KINDS.policy_feedback,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                },
                {
                    'policy_areas': ['This field is required.'],
                    'policy_issue_type': ['This field is required.'],
                    'communication_channel': ['This field is required.'],
                }
            ),

            # fields not allowed
            (
                {
                    'kind': Interaction.KINDS.policy_feedback,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),
                    'policy_areas': [partial(random_obj_for_model, PolicyArea)],
                    'policy_issue_type': partial(random_obj_for_model, PolicyIssueType),

                    # fields not allowed
                    'investment_project': InvestmentProjectFactory,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',

                },
                {
                    'is_event': ['This field is only valid for service deliveries.'],
                    'event': ['This field is only valid for service deliveries.'],
                    'service_delivery_status': [
                        'This field is only valid for service deliveries.'
                    ],
                    'grant_amount_offered': ['This field is only valid for service deliveries.'],
                    'net_company_receipt': ['This field is only valid for service deliveries.'],
                    'investment_project': ['This field is only valid for interactions.']
                }
            ),

            # both policy area and policy areas provided
            (
                {
                    'kind': Interaction.KINDS.policy_feedback,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'communication_channel': partial(random_obj_for_model,
                                                     CommunicationChannel),
                    'policy_area': partial(random_obj_for_model, PolicyArea),
                    'policy_areas': [partial(random_obj_for_model, PolicyArea)],
                    'policy_issue_type': partial(random_obj_for_model, PolicyIssueType),

                    # fields not allowed
                    'investment_project': InvestmentProjectFactory,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',

                },
                {
                    api_settings.NON_FIELD_ERRORS_KEY: [
                        'Only one of policy_area and policy_areas should be provided.',
                    ]
                }
            ),
        )
    )
    def test_validation(self, data, errors):
        """Test validation errors."""
        data = resolve_data(data)
        url = reverse('api-v3:interaction:collection')
        user = create_add_policy_feedback_user()
        api_client = self.create_api_client(user=user)
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors

    @pytest.mark.parametrize(
        'create_user',
        (
            create_interaction_user_without_policy_feedback,
            create_restricted_investment_project_user,
        )
    )
    def test_add_without_permission(self, create_user):
        """Test adding a policy feedback interaction without the required permissions."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        policy_area = random_obj_for_model(PolicyArea)
        policy_issue_type = random_obj_for_model(PolicyIssueType)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.policy_feedback,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
            'policy_areas': [policy_area.pk],
            'policy_issue_type': policy_issue_type.pk
        }
        user = create_user()
        api_client = self.create_api_client(user=user)
        response = api_client.post(url, request_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'kind': ['You don’t have permission to add this type of interaction.']
        }


class TestUpdatePolicyFeedback(APITestMixin):
    """Tests for the update policy feedback view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_update(self):
        """Test updating a policy feedback interaction."""
        interaction = PolicyFeedbackFactory()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        user = create_change_policy_feedback_user()
        api_client = self.create_api_client(user=user)
        response = api_client.patch(url, {'notes': 'updated notes'})

        first_policy_area = interaction.policy_areas.first()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(interaction.pk),
            'kind': interaction.kind,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': {
                'id': str(first_policy_area.pk),
                'name': first_policy_area.name,
            },
            'policy_areas': [{
                'id': str(first_policy_area.pk),
                'name': first_policy_area.name,
            }],
            'policy_issue_type': {
                'id': str(interaction.policy_issue_type.pk),
                'name': interaction.policy_issue_type.name
            },
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name
            },
            'subject': interaction.subject,
            'date': format_date_or_datetime(interaction.date.date()),
            'dit_adviser': {
                'id': str(interaction.dit_adviser.pk),
                'first_name': interaction.dit_adviser.first_name,
                'last_name': interaction.dit_adviser.last_name,
                'name': interaction.dit_adviser.name
            },
            'notes': 'updated notes',
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name
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
                'id': str(interaction.service.id),
                'name': interaction.service.name,
            },
            'dit_team': {
                'id': str(interaction.dit_team.id),
                'name': interaction.dit_team.name,
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
                'id': str(user.pk),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': user.name
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    @pytest.mark.parametrize(
        'create_user',
        (
            create_interaction_user_without_policy_feedback,
            create_restricted_investment_project_user,
        )
    )
    def test_update_without_permission(self, create_user):
        """Test updating a policy feedback interaction without the required permissions."""
        interaction = PolicyFeedbackFactory()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        user = create_user()
        api_client = self.create_api_client(user=user)
        response = api_client.patch(url, {'notes': 'updated notes'})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'You do not have permission to perform this action.'
        }


class TestGetPolicyFeedback(APITestMixin):
    """Tests for the retrieve policy feedback view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_get(self):
        """Test retrieving a policy feedback interaction."""
        interaction = PolicyFeedbackFactory()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        user = create_read_policy_feedback_user()
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        first_policy_area = interaction.policy_areas.first()

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'id': str(interaction.pk),
            'kind': interaction.kind,
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_area': {
                'id': str(first_policy_area.pk),
                'name': first_policy_area.name,
            },
            'policy_areas': [{
                'id': str(first_policy_area.pk),
                'name': first_policy_area.name,
            }],
            'policy_issue_type': {
                'id': str(interaction.policy_issue_type.pk),
                'name': interaction.policy_issue_type.name
            },
            'communication_channel': {
                'id': str(interaction.communication_channel.pk),
                'name': interaction.communication_channel.name
            },
            'subject': interaction.subject,
            'date': format_date_or_datetime(interaction.date.date()),
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
                'name': interaction.contact.name,
                'first_name': interaction.contact.first_name,
                'last_name': interaction.contact.last_name,
                'job_title': interaction.contact.job_title,
            },
            'event': None,
            'service': {
                'id': str(interaction.service.id),
                'name': interaction.service.name,
            },
            'dit_team': {
                'id': str(interaction.dit_team.id),
                'name': interaction.dit_team.name,
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
            'modified_on': '2017-04-18T13:25:30.986208Z',
        }

    @pytest.mark.parametrize(
        'create_user',
        (
            create_interaction_user_without_policy_feedback,
            create_restricted_investment_project_user,
        )
    )
    def test_get_without_permission(self, create_user):
        """Test retrieving a policy feedback interaction without the required permissions."""
        interaction = PolicyFeedbackFactory()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        user = create_user()
        api_client = self.create_api_client(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            'detail': 'You do not have permission to perform this action.'
        }
