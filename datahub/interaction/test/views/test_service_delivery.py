from datetime import date
from functools import partial

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service
from datahub.core.test_utils import APITestMixin, random_obj_for_model
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import (
    CommunicationChannel,
    Interaction, PolicyArea,
    PolicyIssueType,
    ServiceDeliveryStatus,
)
from datahub.interaction.test.factories import (
    EventServiceDeliveryFactory,
    ServiceDeliveryFactory,
)
from datahub.interaction.test.views.utils import resolve_data
from datahub.investment.project.test.factories import InvestmentProjectFactory


class TestAddServiceDelivery(APITestMixin):
    """Tests for the add service delivery view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize(
        'extra_data',
        (
            # non-event service delivery
            {
                'is_event': False,
            },
            # event service delivery
            {
                'is_event': True,
                'event': EventFactory,
            },
            # non-event service delivery with theme
            {
                'is_event': False,
                'theme': Interaction.THEMES.export,
            },
            # non-event service delivery with blank notes
            {
                'is_event': False,
                'notes': '',
            },
            # non-event service delivery with all fields filled in
            {
                'is_event': False,
                'notes': 'hello',
                'service_delivery_status': partial(random_obj_for_model, ServiceDeliveryStatus),
                'grant_amount_offered': '9999.99',
                'net_company_receipt': '8888.99',
            },
            # non-event service delivery with policy feedback
            {
                'is_event': False,
                'was_policy_feedback_provided': True,
                'policy_areas': [
                    partial(random_obj_for_model, PolicyArea),
                ],
                'policy_feedback_notes': 'Policy feedback notes',
                'policy_issue_types': [partial(random_obj_for_model, PolicyIssueType)],
            },
            # Interaction with a status
            {
                'is_event': False,
                'status': Interaction.STATUSES.draft,
            },
        ),
    )
    def test_add(self, extra_data):
        """Test add a new service delivery."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory(company=company)
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': adviser.pk},
            ],
            'company': company.pk,
            'contacts': [contact.pk],
            'service': Service.trade_enquiry.value.id,
            'was_policy_feedback_provided': False,

            **resolve_data(extra_data),
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.service_delivery,
            'status': request_data.get('status', Interaction.STATUSES.complete),
            'theme': request_data.get('theme', None),
            'is_event': request_data['is_event'],
            'service_delivery_status': request_data.get('service_delivery_status'),
            'grant_amount_offered': request_data.get('grant_amount_offered'),
            'net_company_receipt': request_data.get('net_company_receipt'),
            'communication_channel': None,
            'policy_areas': request_data.get('policy_areas', []),
            'policy_feedback_notes': request_data.get('policy_feedback_notes', ''),
            'policy_issue_types':
                request_data.get('policy_issue_types', []),
            'was_policy_feedback_provided':
                request_data.get('was_policy_feedback_provided', False),
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
                        'id': str(adviser.dit_team.pk),
                        'name': adviser.dit_team.name,
                    },
                },
            ],
            'dit_team': {
                'id': str(adviser.dit_team.pk),
                'name': adviser.dit_team.name,
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
            'event': request_data.get('event'),
            'service': {
                'id': str(Service.trade_enquiry.value.id),
                'name': Service.trade_enquiry.value.name,
            },
            'investment_project': None,
            'archived_documents_url_path': '',
            'created_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'modified_by': {
                'id': str(self.user.pk),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'name': self.user.name,
            },
            'created_on': '2017-04-18T13:25:30.986208Z',
            'modified_on': '2017-04-18T13:25:30.986208Z',
            'location': '',
            'archived': False,
            'archived_by': None,
            'archived_on': None,
            'archived_reason': None,
        }

    @pytest.mark.parametrize(
        'data,errors',
        (
            # required fields
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                },
                {
                    'contacts': ['This field is required.'],
                    'date': ['This field is required.'],
                    'dit_participants': ['This field is required.'],
                    'subject': ['This field is required.'],
                    'company': ['This field is required.'],
                    'was_policy_feedback_provided': ['This field is required.'],
                },
            ),

            # required fields for service delivery
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'was_policy_feedback_provided': False,
                },
                {
                    'service': ['This field is required.'],
                    'is_event': ['This field is required.'],
                },
            ),

            # policy feedback fields cannot be omitted when policy feedback provided
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),

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
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),

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
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    'was_policy_feedback_provided': False,

                    # fields not allowed
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),
                    'policy_areas': [partial(random_obj_for_model, PolicyArea)],
                    'policy_feedback_notes': 'Policy feedback notes.',
                    'policy_issue_types': [partial(random_obj_for_model, PolicyIssueType)],
                    'investment_project': InvestmentProjectFactory,
                },
                {
                    'communication_channel': ['This field is not valid for service deliveries.'],
                    'policy_areas': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'policy_feedback_notes': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'policy_issue_types': [
                        'This field is only valid when policy feedback has been provided.',
                    ],
                    'investment_project': ['This field is only valid for interactions.'],
                },
            ),

            # fields where None is not allowed
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': None,
                    'service': Service.trade_enquiry.value.id,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',

                    # fields where None is not allowed
                    'was_policy_feedback_provided': None,
                    'policy_feedback_notes': None,
                },
                {
                    'dit_participants': ['This field may not be null.'],
                    'was_policy_feedback_provided': ['This field may not be null.'],
                    'policy_feedback_notes': ['This field may not be null.'],
                },
            ),

            # theme=investment not allowed
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    'was_policy_feedback_provided': False,
                    'is_event': False,

                    'theme': Interaction.THEMES.investment,
                },
                {
                    'kind': ["This value can't be selected for investment interactions."],
                },
            ),

            # event field not allowed for non-event service delivery
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'notes': 'hello',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    'was_policy_feedback_provided': False,

                    # 'is_event' is False so 'event' should be empty
                    'is_event': False,
                    'event': EventFactory,
                },
                {
                    'event': ['This field is only valid for event service deliveries.'],
                },
            ),

            # event field required for event service delivery
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    'was_policy_feedback_provided': False,

                    # 'is_event' is False so 'event' should be set
                    'is_event': True,
                },
                {
                    'event': ['This field is required.'],
                },
            ),

            # multiple contacts not allowed for event service delivery
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],
                    'service': Service.trade_enquiry.value.id,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',
                    'was_policy_feedback_provided': False,
                    'is_event': True,
                    'event': EventFactory,

                    # multiple contacts should not be allowed
                    'contacts': [ContactFactory, ContactFactory],
                },
                {
                    'contacts': ['Only one contact can be provided for event service deliveries.'],
                },
            ),

            # dit_participants cannot be empty list
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contacts': [ContactFactory],
                    'service': Service.trade_enquiry.value.id,
                    'was_policy_feedback_provided': False,

                    'dit_participants': [],
                },
                {
                    'dit_participants': {
                        api_settings.NON_FIELD_ERRORS_KEY: ['This list may not be empty.'],
                    },
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


class TestUpdateServiceDelivery(APITestMixin):
    """Tests for the update interaction view."""

    def test_change_non_event_service_delivery_to_event(self):
        """Test making a non-event service delivery an event service delivery."""
        service_delivery = ServiceDeliveryFactory()
        event = EventFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': service_delivery.pk})
        response = self.api_client.patch(
            url,
            data={
                'is_event': True,
                'event': event.pk,
            },
        )

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
        response = self.api_client.patch(
            url,
            data={
                'is_event': False,
                'event': None,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['is_event'] is False
        assert response_data['event'] is None

    def test_cannot_add_more_contacts_to_event_service_delivery(self):
        """Test that an event service delivery cannot be updated to have multiple contacts."""
        service_delivery = EventServiceDeliveryFactory()
        new_contacts = ContactFactory.create_batch(2, company=service_delivery.company)

        url = reverse('api-v3:interaction:item', kwargs={'pk': service_delivery.pk})
        request_data = {
            'contacts': [{'id': contact.pk} for contact in new_contacts],
        }
        response = self.api_client.patch(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'contacts': ['Only one contact can be provided for event service deliveries.'],
        }

    def test_fails_with_negative_grant_amount(self):
        """Test validation when an a negative grant amount offered is entered."""
        interaction = ServiceDeliveryFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data={
                'grant_amount_offered': '-100.00',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['grant_amount_offered'] == [
            'Ensure this value is greater than or equal to 0.',
        ]

    def test_fails_with_negative_net_company_receipt(self):
        """Test validation when an a negative net company receipt is entered."""
        interaction = ServiceDeliveryFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data={
                'net_company_receipt': '-100.00',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['net_company_receipt'] == [
            'Ensure this value is greater than or equal to 0.',
        ]
