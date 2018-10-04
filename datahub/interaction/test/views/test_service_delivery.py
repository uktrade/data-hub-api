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
from ..factories import (
    EventServiceDeliveryFactory, ServiceDeliveryFactory,
)
from ...models import (
    CommunicationChannel, Interaction, PolicyArea, PolicyIssueType, ServiceDeliveryStatus,
)


class TestAddServiceDelivery(APITestMixin):
    """Tests for the add service delivery view."""

    @freeze_time('2017-04-18 13:25:30.986208')
    @pytest.mark.parametrize(
        'extra_data',
        (
            # non-event service delivery
            {
                'is_event': False,
                'notes': 'hello',
            },
            # event service delivery
            {
                'is_event': True,
                'event': EventFactory,
            },
            # non-event service delivery with all fields filled in
            {
                'is_event': False,
                'notes': 'hello',
                'service_delivery_status': partial(random_obj_for_model, ServiceDeliveryStatus),
                'grant_amount_offered': '9999.99',
                'net_company_receipt': '8888.99',
            },
        ),
    )
    def test_add(self, extra_data):
        """Test add a new service delivery."""
        adviser = AdviserFactory()
        company = CompanyFactory()
        contact = ContactFactory()
        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.service_delivery,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': adviser.pk,
            'company': company.pk,
            'contact': contact.pk,
            'service': Service.trade_enquiry.value.id,
            'dit_team': Team.healthcare_uk.value.id,

            **resolve_data(extra_data),
        }
        response = self.api_client.post(url, request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data == {
            'id': response_data['id'],
            'kind': Interaction.KINDS.service_delivery,
            'is_event': request_data['is_event'],
            'service_delivery_status': request_data.get('service_delivery_status'),
            'grant_amount_offered': request_data.get('grant_amount_offered'),
            'net_company_receipt': request_data.get('net_company_receipt'),
            'communication_channel': None,
            'policy_areas': [],
            'policy_issue_type': None,
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
            'event': request_data.get('event'),
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
                    'date': ['This field is required.'],
                    'subject': ['This field is required.'],
                    'company': ['This field is required.'],
                    'contact': ['This field is required.'],
                    'dit_adviser': ['This field is required.'],
                    'service': ['This field is required.'],
                    'dit_team': ['This field is required.'],
                },
            ),

            # required fields for service delivery
            (
                {
                    'kind': Interaction.KINDS.service_delivery,
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'company': CompanyFactory,
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                },
                {
                    'is_event': ['This field is required.'],
                    'notes': ['This field is required.'],
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
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'is_event': True,
                    'event': EventFactory,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',

                    # fields not allowed
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),
                    'policy_areas': [partial(random_obj_for_model, PolicyArea)],
                    'policy_issue_type': partial(random_obj_for_model, PolicyIssueType),
                    'investment_project': InvestmentProjectFactory,
                },
                {
                    'communication_channel': ['This field is not valid for service deliveries.'],
                    'policy_areas': ['This field is only valid for policy feedback.'],
                    'policy_issue_type': ['This field is only valid for policy feedback.'],
                    'investment_project': ['This field is only valid for interactions.'],
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
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',

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
                    'contact': ContactFactory,
                    'dit_adviser': AdviserFactory,
                    'service': Service.trade_enquiry.value.id,
                    'dit_team': Team.healthcare_uk.value.id,
                    'service_delivery_status': partial(
                        random_obj_for_model, ServiceDeliveryStatus,
                    ),
                    'grant_amount_offered': '1111.11',
                    'net_company_receipt': '8888.11',

                    # 'is_event' is False so 'event' should be set
                    'is_event': True,
                },
                {
                    'event': ['This field is required.'],
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
