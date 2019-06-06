from datetime import date

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.constants import (
    Service as ServiceConstant,
    ServiceAdditionalQuestion as ServiceAdditionalQuestionConstant,
    ServiceAnswerOption as ServiceAnswerOptionConstant,
    ServiceQuestion as ServiceQuestionConstant,
    Team as TeamConstant,
)
from datahub.core.test_utils import APITestMixin, create_test_user, random_obj_for_model
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction,
)
from datahub.interaction.test.permissions import (
    NON_RESTRICTED_ADD_PERMISSIONS,
)
from datahub.interaction.test.views.utils import resolve_data
from datahub.metadata.models import Service


GLOBAL_GROWTH_SERVICE_ANSWERS_ALL_OPTIONAL = {
    ServiceQuestionConstant.ggs_status.value.id: {
        ServiceAnswerOptionConstant.ggs_completed.value.id: {
            ServiceAdditionalQuestionConstant.ggs_completed_grant_offered.value.id: 5000,
            ServiceAdditionalQuestionConstant.ggs_completed_net_receipt.value.id: 2000,
        },
    },
}


GLOBAL_GROWTH_SERVICE_ANSWERS_ONE_OPTIONAL = {
    ServiceQuestionConstant.ggs_status.value.id: {
        ServiceAnswerOptionConstant.ggs_completed.value.id: {
            ServiceAdditionalQuestionConstant.ggs_completed_net_receipt.value.id: 2000,
        },
    },
}


GLOBAL_GROWTH_SERVICE_ANSWERS_NO_OPTIONAL = {
    ServiceQuestionConstant.ggs_status.value.id: {
        ServiceAnswerOptionConstant.ggs_completed.value.id: {},
    },
}


class TestAddInteraction(APITestMixin):
    """Tests for the add interaction view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'service,extra_data',
        (
            (
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': {
                        ServiceQuestionConstant.piai_what_did_you_give_advice_about.value.id: {
                            ServiceAnswerOptionConstant.piai_banking_and_funding.value.id: {},
                        },
                        ServiceQuestionConstant.piai_was_this_of_significant_assistance.value.id: {
                            ServiceAnswerOptionConstant.piai_yes.value.id: {},
                        },
                    },
                },
            ),
            (
                ServiceConstant.global_growth_service.value.id,
                {
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_ALL_OPTIONAL,
                },
            ),
            (
                ServiceConstant.global_growth_service.value.id,
                {
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_ONE_OPTIONAL,
                },
            ),
            (
                ServiceConstant.global_growth_service.value.id,
                {
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_NO_OPTIONAL,
                },
            ),
        ),
    )
    def test_add(self, service, extra_data, permissions):
        """Test add a new interaction."""
        adviser = create_test_user(permission_codenames=permissions)
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'company': company.pk,
            'contacts': [contact.pk],
            'service': service,
            'dit_team': TeamConstant.healthcare_uk.value.id,
            'was_policy_feedback_provided': False,

            **resolve_data(extra_data),
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        service = Service.objects.get(pk=service)

        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.interaction,
            'status': request_data.get('status', Interaction.STATUSES.complete),
            'theme': request_data.get('theme', None),
            'is_event': None,
            'service_delivery_status': None,
            'grant_amount_offered': None,
            'net_company_receipt': None,
            'policy_areas': request_data.get('policy_areas', []),
            'policy_feedback_notes': request_data.get('policy_feedback_notes', ''),
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
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(adviser.pk),
                        'first_name': adviser.first_name,
                        'last_name': adviser.last_name,
                        'name': adviser.name,
                    },
                    'team': {
                        'id': str(TeamConstant.healthcare_uk.value.id),
                        'name': TeamConstant.healthcare_uk.value.name,
                    },
                },
            ],
            'dit_team': {
                'id': str(TeamConstant.healthcare_uk.value.id),
                'name': TeamConstant.healthcare_uk.value.name,
            },
            'notes': request_data.get('notes', ''),
            'company': {
                'id': str(company.pk),
                'name': company.name,
            },
            'contacts': [{
                'id': str(contact.pk),
                'name': contact.name,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'job_title': contact.job_title,
            }],
            'event': None,
            'service': {
                'id': str(service.id),
                'name': service.name,
            },
            'service_answers': extra_data['service_answers'],
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
            'location': request_data.get('location', ''),
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'service,extra_data,expected_response',
        (
            (  # give answers to service that does not require them
                ServiceConstant.account_management.value.id,
                {
                    'service_answers': {
                        ServiceQuestionConstant.piai_what_did_you_give_advice_about.value.id: {
                            ServiceAnswerOptionConstant.piai_banking_and_funding.value.id: {},
                        },
                        ServiceQuestionConstant.piai_was_this_of_significant_assistance.value.id: {
                            ServiceAnswerOptionConstant.piai_yes.value.id: {},
                        },
                    },
                },
                {
                    'service_answers': ['Answers not required for given service value.'],
                },
            ),
            (  # give answers to service different than selected
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_ALL_OPTIONAL,
                },
                {
                    ServiceQuestionConstant.ggs_status.value.id: [
                        'This question does not relate to selected service.',
                    ],
                    ServiceQuestionConstant.piai_what_did_you_give_advice_about.value.id: [
                        'This field is required.',
                    ],
                    ServiceQuestionConstant.piai_was_this_of_significant_assistance.value.id: [
                        'This field is required.',
                    ],
                },
            ),
            (  # give more than one answer option
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': {
                        ServiceQuestionConstant.piai_what_did_you_give_advice_about.value.id: {
                            ServiceAnswerOptionConstant.piai_banking_and_funding.value.id: {},
                            ServiceAnswerOptionConstant.piai_dit_or_government_services.value.id: {
                            },
                        },
                        ServiceQuestionConstant.piai_was_this_of_significant_assistance.value.id: {
                            ServiceAnswerOptionConstant.piai_yes.value.id: {},
                        },
                    },
                },
                {
                    ServiceQuestionConstant.piai_what_did_you_give_advice_about.value.id: [
                        'Only one answer can be selected for this question.',
                    ],
                },
            ),
        ),
    )
    def test_cannot_add(self, service, extra_data, expected_response, permissions):
        """Test that interaction with incorrect answers cannot be added."""
        adviser = create_test_user(permission_codenames=permissions)
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'company': company.pk,
            'contacts': [contact.pk],
            'service': service,
            'dit_team': TeamConstant.healthcare_uk.value.id,
            'was_policy_feedback_provided': False,

            **resolve_data(extra_data),
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data == expected_response
