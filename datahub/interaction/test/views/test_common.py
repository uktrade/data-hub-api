from datetime import date, datetime

import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin, create_test_user, format_date_or_datetime, random_obj_for_model
)
from datahub.event.test.factories import EventFactory
from datahub.investment.test.factories import InvestmentProjectFactory
from datahub.metadata.test.factories import TeamFactory
from ..factories import CompanyInteractionFactory, EventServiceDeliveryFactory
from ...models import CommunicationChannel, Interaction


class TestGetInteraction(APITestMixin):
    """Base tests for the get interaction view."""

    def test_fails_without_permissions(self):
        """Should return 403"""
        interaction = CompanyInteractionFactory()
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateInteraction(APITestMixin):
    """Base tests for the update interaction view."""

    def test_cannot_update_read_only_fields(self):
        """Test updating read-only fields."""
        interaction = CompanyInteractionFactory(
            archived_documents_url_path='old_path',
        )

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, format='json', data={
            'archived_documents_url_path': 'new_path'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived_documents_url_path'] == 'old_path'

    def test_date_validation(self):
        """Test validation when an invalid date is provided."""
        interaction = CompanyInteractionFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'date': 'abcd-de-fe',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['date'] == [
            'Datetime has wrong format. Use one of these formats instead: YYYY-MM-DD.'
        ]


class TestListInteractions(APITestMixin):
    """Tests for the list interactions view."""

    def test_filtered_by_company(self):
        """List of interactions filtered by company"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        CompanyInteractionFactory.create_batch(3, company=company1)
        interactions = CompanyInteractionFactory.create_batch(2, company=company2)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {'company_id': company2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_filtered_by_contact(self):
        """List of interactions filtered by contact"""
        contact1 = ContactFactory()
        contact2 = ContactFactory()

        CompanyInteractionFactory.create_batch(3, contact=contact1)
        interactions = CompanyInteractionFactory.create_batch(2, contact=contact2)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {'contact_id': contact2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_filtered_by_investment_project(self):
        """List of interactions filtered by investment project"""
        contact = ContactFactory()
        project = InvestmentProjectFactory()
        company = CompanyFactory()

        CompanyInteractionFactory.create_batch(3, contact=contact)
        CompanyInteractionFactory.create_batch(3, company=company)
        project_interactions = CompanyInteractionFactory.create_batch(
            2, investment_project=project
        )

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {
            'investment_project_id': project.id
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 2
        actual_ids = {i['id'] for i in response_data['results']}
        expected_ids = {str(i.id) for i in project_interactions}
        assert actual_ids == expected_ids

    def test_filtered_by_event(self):
        """List of interactions filtered by event"""
        contact = ContactFactory()
        event = EventFactory()

        CompanyInteractionFactory.create_batch(3, contact=contact)
        EventServiceDeliveryFactory.create_batch(3)
        service_deliveries = EventServiceDeliveryFactory.create_batch(3, event=event)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, {'event_id': event.id})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3

        actual_ids = {result['id'] for result in response_data['results']}
        expected_ids = {str(service_delivery.id) for service_delivery in service_deliveries}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'sort', ('last_name', 'first_name')
    )
    def test_sort_by_contact_names(self, sort):
        """List of interactions sorted by contact name"""
        interactions = EventServiceDeliveryFactory.create_batch(3)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, data={
            'sortby': f'contact__{sort}',
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)
        expected_names = sorted(getattr(interaction.contact, sort) for interaction in interactions)
        actual_names = [result['contact'][sort] for result in response_data['results']]
        assert expected_names == actual_names

    def test_sort_by_created_on(self):
        """Test sorting by created_on."""
        creation_times = [
            datetime(2015, 1, 1),
            datetime(2016, 1, 1),
            datetime(2019, 1, 1),
            datetime(2020, 1, 1),
            datetime(2005, 1, 1),
        ]

        for creation_time in creation_times:
            with freeze_time(creation_time):
                EventServiceDeliveryFactory()

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, data={
            'sortby': 'created_on',
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(creation_times)
        expected_timestamps = [
            format_date_or_datetime(creation_time)
            for creation_time in sorted(creation_times)
        ]
        actual_timestamps = [result['created_on'] for result in response_data['results']]
        assert expected_timestamps == actual_timestamps


class TestInteractionVersioning(APITestMixin):
    """
    Tests for versions created when interacting with the interaction endpoints.
    """

    def test_add_creates_a_new_version(self):
        """Test that creating an interaction creates a new version."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse('api-v3:interaction:collection'),
            data={
                'kind': Interaction.KINDS.interaction,
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_adviser': AdviserFactory().pk,
                'notes': 'hello',
                'company': CompanyFactory().pk,
                'contact': ContactFactory().pk,
                'service': Service.trade_enquiry.value.id,
                'dit_team': Team.healthcare_uk.value.id
            },
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subject'] == 'whatever'

        interaction = Interaction.objects.get(pk=response.data['id'])

        # check version created
        assert Version.objects.get_for_object(interaction).count() == 1
        version = Version.objects.get_for_object(interaction).first()
        assert version.revision.user == self.user
        assert version.field_dict['subject'] == 'whatever'
        assert not any(set(version.field_dict) & set(EXCLUDED_BASE_MODEL_FIELDS))

    def test_add_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        assert Version.objects.count() == 0

        response = self.api_client.post(
            reverse('api-v3:interaction:collection'),
            data={
                'kind': Interaction.KINDS.interaction,
            },
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.count() == 0

    def test_update_creates_a_new_version(self):
        """Test that updating an interaction creates a new version."""
        service_delivery = EventServiceDeliveryFactory()

        assert Version.objects.get_for_object(service_delivery).count() == 0

        response = self.api_client.patch(
            reverse('api-v3:interaction:item', kwargs={'pk': service_delivery.pk}),
            data={'subject': 'new subject'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'new subject'

        # check version created
        assert Version.objects.get_for_object(service_delivery).count() == 1
        version = Version.objects.get_for_object(service_delivery).first()
        assert version.revision.user == self.user
        assert version.field_dict['subject'] == 'new subject'

    def test_update_400_doesnt_create_a_new_version(self):
        """Test that if the endpoint returns 400, no version is created."""
        service_delivery = EventServiceDeliveryFactory()

        assert Version.objects.get_for_object(service_delivery).count() == 0

        response = self.api_client.patch(
            reverse('api-v3:interaction:item', kwargs={'pk': service_delivery.pk}),
            data={'kind': 'invalid'},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(service_delivery).count() == 0
