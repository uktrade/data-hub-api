from datetime import date
from operator import itemgetter

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
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InvestmentProjectInteractionFactory,
)
from datahub.interaction.test.permissions import (
    NON_RESTRICTED_ADD_PERMISSIONS,
    NON_RESTRICTED_VIEW_PERMISSIONS,
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


class TestServiceAnswers(APITestMixin):
    """Tests for the interaction service answers."""

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

    @pytest.mark.parametrize(
        'initial_value,new_value',
        (
            (
                {
                    'service_id': ServiceConstant.global_growth_service.value.id,
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_NO_OPTIONAL,
                },
                {
                    'service': ServiceConstant.global_growth_service.value.id,
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_ALL_OPTIONAL,
                },
            ),
            (
                {
                    'service_id': ServiceConstant.global_growth_service.value.id,
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_ALL_OPTIONAL,
                },
                {
                    'service':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
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
        ),
    )
    def test_update_service_answers(self, initial_value, new_value):
        """Test that the service answers field can be updated."""
        interaction = CompanyInteractionFactory(**initial_value)

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data=new_value,
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['service']['id'] == new_value['service']
        assert response_data['service_answers'] == new_value['service_answers']

    @pytest.mark.parametrize(
        'initial_value,new_value,expected_response',
        (
            (
                {
                    'service_id': ServiceConstant.global_growth_service.value.id,
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_NO_OPTIONAL,
                },
                {
                    'service':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
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
            (
                {
                    'service_id': ServiceConstant.global_growth_service.value.id,
                    'service_answers': GLOBAL_GROWTH_SERVICE_ANSWERS_ALL_OPTIONAL,
                },
                {
                    'service':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {},
                },
                {'service_answers': ['This field is required.']},
            ),
        ),
    )
    def test_cannot_update_service_answers(self, initial_value, new_value, expected_response):
        """Test that the service answers field cannot be updated with incorrect data."""
        interaction = CompanyInteractionFactory(**initial_value)

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data=new_value,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == expected_response

    @pytest.mark.parametrize('permissions', NON_RESTRICTED_VIEW_PERMISSIONS)
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_non_restricted_user_can_get_interaction_with_service_answers(
        self,
        permissions,
    ):
        """Test that a non-restricted user can get interaction with service answers."""
        requester = create_test_user(permission_codenames=permissions)

        extra_data = {
            'service_id': ServiceConstant.providing_investment_advice_and_information.value.id,
            'service_answers': {
                ServiceQuestionConstant.piai_what_did_you_give_advice_about.value.id: {
                    ServiceAnswerOptionConstant.piai_banking_and_funding.value.id: {},
                },
                ServiceQuestionConstant.piai_was_this_of_significant_assistance.value.id: {
                    ServiceAnswerOptionConstant.piai_yes.value.id: {},
                },
            },
        }
        interaction = InvestmentProjectInteractionFactory(**extra_data)
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        response_data['contacts'].sort(key=itemgetter('id'))
        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.interaction,
            'status': Interaction.STATUSES.complete,
            'theme': interaction.theme,
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
            'dit_participants': [
                {
                    'adviser': {
                        'id': str(interaction.dit_adviser.pk),
                        'first_name': interaction.dit_adviser.first_name,
                        'last_name': interaction.dit_adviser.last_name,
                        'name': interaction.dit_adviser.name,
                    },
                    'team': {
                        'id': str(interaction.dit_team.pk),
                        'name': interaction.dit_team.name,
                    },
                },
            ],
            'dit_team': {
                'id': str(interaction.dit_team.pk),
                'name': interaction.dit_team.name,
            },
            'notes': interaction.notes,
            'company': {
                'id': str(interaction.company.pk),
                'name': interaction.company.name,
            },
            'contacts': [
                {
                    'id': str(contact.pk),
                    'name': contact.name,
                    'first_name': contact.first_name,
                    'last_name': contact.last_name,
                    'job_title': contact.job_title,
                }
                for contact in interaction.contacts.order_by('pk')
            ],
            'event': None,
            'service': {
                'id': str(ServiceConstant.providing_investment_advice_and_information.value.id),
                'name': ServiceConstant.providing_investment_advice_and_information.value.name,
            },
            'service_answers': extra_data['service_answers'],
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
            'location': '',
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
        }
