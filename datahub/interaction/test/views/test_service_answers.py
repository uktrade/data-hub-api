from datetime import date

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import ContactFactory
from datahub.core.constants import Service as ServiceConstant
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
from datahub.interaction.test.views.constants import ServiceAnswerOptionID, ServiceQuestionID
from datahub.interaction.test.views.utils import resolve_data
from datahub.metadata.models import Service
from datahub.metadata.test.factories import TeamFactory


class TestServiceAnswers(APITestMixin):
    """Tests for the interaction service answers."""

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    def test_add(self, permissions):
        """Test add a new interaction."""
        adviser = create_test_user(
            permission_codenames=permissions,
            dit_team=TeamFactory(),
        )
        contact = ContactFactory()
        communication_channel = random_obj_for_model(CommunicationChannel)
        service = Service.objects.get(
            pk=ServiceConstant.providing_investment_advice_and_information.value.id,
        )

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [{
                'adviser': adviser.pk,
            }],
            'company': contact.company.pk,
            'contacts': [contact.pk],
            'was_policy_feedback_provided': False,
            'export_countries': [],
            'service': service.pk,
            'service_answers': {
                ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                    ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                },
            },
        }

        api_client = self.create_api_client(user=adviser)
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data['service'] == {
            'id': str(service.id),
            'name': service.name,
        }
        assert response_data['service_answers'] == request_data['service_answers']

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize('permissions', NON_RESTRICTED_ADD_PERMISSIONS)
    @pytest.mark.parametrize(
        'service,extra_data,expected_response',
        (
            pytest.param(
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': [],
                },
                {
                    'service_answers': ['Answers have invalid format.'],
                },
                id='wrong service_answers type',
            ),
            pytest.param(
                ServiceConstant.account_management.value.id,
                {
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service_answers': ['Answers not required for given service value.'],
                },
                id='give answers to service that does not require them',
            ),
            pytest.param(
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': {
                        ServiceQuestionID.making_export_introductions.value: {
                            ServiceAnswerOptionID.making_export_introductions_customers.value: {},
                        },
                    },
                },
                {
                    ServiceQuestionID.making_export_introductions.value: [
                        'This question does not relate to selected service.',
                    ],
                    ServiceQuestionID.piai_what_did_you_give_advice_about.value: [
                        'This field is required.',
                    ],
                },
                id='give answers to service different than selected',
            ),
            pytest.param(
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {},
                    },
                },
                {
                    ServiceQuestionID.piai_what_did_you_give_advice_about.value: [
                        'This field is required.',
                    ],
                },
                id='omit answer option',
            ),
            pytest.param(
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.making_export_introductions_customers.value,
                        },
                    },
                },
                {
                    ServiceAnswerOptionID.making_export_introductions_customers.value: [
                        'The selected answer option is not valid for this question.',
                    ],
                },
                id='give answer option for a different question',
            ),
            pytest.param(
                ServiceConstant.providing_investment_advice_and_information.value.id,
                {
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                            ServiceAnswerOptionID.piai_dit_or_government_services.value: {},
                        },
                    },
                },
                {
                    ServiceQuestionID.piai_what_did_you_give_advice_about.value: [
                        'Only one answer can be selected for this question.',
                    ],
                },
                id='give more than one answer option',
            ),
        ),
    )
    def test_cannot_add(self, service, extra_data, expected_response, permissions):
        """Test that interaction with incorrect answers cannot be added."""
        adviser = create_test_user(permission_codenames=permissions)
        contact = ContactFactory()
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [{
                'adviser': adviser.pk,
            }],
            'company': contact.company.pk,
            'contacts': [contact.pk],
            'was_policy_feedback_provided': False,

            'service': service,
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
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_dit_or_government_services.value: {},
                        },
                    },
                },
                id='change to different answer',
            ),
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.making_export_introductions.value.id,
                    'service_answers': {
                        ServiceQuestionID.making_export_introductions.value: {
                            ServiceAnswerOptionID.making_export_introductions_customers.value: {},
                        },
                    },
                },
                id='change to different service and answer',
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
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.account_management.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service_answers': [
                        'Answers not required for given service value.',
                    ],
                },
                id='change service, give unneeded answer',
            ),
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.making_export_introductions.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    ServiceQuestionID.piai_what_did_you_give_advice_about.value: [
                        'This question does not relate to selected service.',
                    ],
                    ServiceQuestionID.making_export_introductions.value: [
                        'This field is required.',
                    ],
                },
                id='change service, give wrong question and answer',
            ),
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {},
                    },
                },
                {
                    ServiceQuestionID.piai_what_did_you_give_advice_about.value: [
                        'This field is required.',
                    ],
                },
                id='change service, give question but no answer',
            ),
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_dit_or_government_services.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.making_export_introductions_customers.value: {},
                        },
                    },
                },
                {
                    ServiceAnswerOptionID.making_export_introductions_customers.value: [
                        'The selected answer option is not valid for this question.',
                    ],
                },
                id='change service, give answer for different question',
            ),
            pytest.param(
                {
                    'service_id':
                        ServiceConstant.providing_investment_advice_and_information.value.id,
                    'service_answers': {
                        ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                            ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                        },
                    },
                },
                {
                    'service':
                        ServiceConstant.making_export_introductions.value.id,
                    'service_answers': {},
                },
                {'service_answers': ['This field is required.']},
                id='change service, give empty service_answers',
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
                ServiceQuestionID.piai_what_did_you_give_advice_about.value: {
                    ServiceAnswerOptionID.piai_banking_and_funding.value: {},
                },
            },
        }
        interaction = InvestmentProjectInteractionFactory(**extra_data)
        api_client = self.create_api_client(user=requester)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data['service'] == {
            'id': str(ServiceConstant.providing_investment_advice_and_information.value.id),
            'name': ServiceConstant.providing_investment_advice_and_information.value.name,
        }
        assert response_data['service_answers'] == extra_data['service_answers']
