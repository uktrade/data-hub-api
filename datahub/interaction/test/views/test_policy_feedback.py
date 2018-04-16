from datetime import date

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.test_utils import APITestMixin, random_obj_for_model
from datahub.investment.test.factories import InvestmentProjectFactory
from ...models import CommunicationChannel, Interaction, PolicyArea, PolicyIssueType


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

    def test_fails_with_missing_fields(self):
        """
        Test add new policy feedback interaction without
        required policy_feedback-only fields.
        """
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
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
        }
        response = self.api_client.post(url, request_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'policy_area': ['This field is required.'],
            'policy_issue_type': ['This field is required.'],
            'communication_channel': ['This field is required.'],
        }

    @freeze_time('2017-04-18 13:25:30.986208')
    def test_fails_with_investment_project(self):
        """
        Test add new policy feedback interaction for an investment project.
        This should not be allowed.
        """
        project = InvestmentProjectFactory()
        adviser = AdviserFactory()
        contact = ContactFactory()
        policy_area = random_obj_for_model(PolicyArea)
        policy_issue_type = random_obj_for_model(PolicyIssueType)
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, {
            'kind': Interaction.KINDS.policy_feedback,
            'contact': contact.pk,
            'communication_channel': random_obj_for_model(CommunicationChannel).pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'notes': 'hello',
            'investment_project': project.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,
            'policy_area': policy_area.pk,
            'policy_issue_type': policy_issue_type.pk
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            'investment_project': ['This field is only valid for interactions.']
        }
