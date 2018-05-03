from datetime import date
from functools import partial

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import APITestMixin, random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from .utils import resolve_data
from ...models import (
    CommunicationChannel, Interaction, PolicyArea, PolicyIssueType, ServiceDeliveryStatus
)


class TestAddPolicyFeedback(APITestMixin):
    """Tests for the add policy feedback view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_add(self):
        """Test add new policy feedback interaction."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        policy_area = random_obj_for_model(PolicyArea)
        policy_issue_type = random_obj_for_model(PolicyIssueType)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.policy_feedback,
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
                'id': str(policy_area.pk), 'name': policy_area.name
            },
            'policy_issue_type': {
                'id': str(policy_issue_type.pk), 'name': policy_issue_type.name
            },
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
                    'policy_area': ['This field is required.'],
                    'policy_issue_type': ['This field is required.'],
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
                    'policy_area': partial(random_obj_for_model, PolicyArea),
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
                    'communication_channel': ['This field is only valid for interactions.'],
                    'investment_project': ['This field is only valid for interactions.']
                }
            ),
        )
    )
    def test_validation(self, data, errors):
        """Test validation errors."""
        data = resolve_data(data)
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors
