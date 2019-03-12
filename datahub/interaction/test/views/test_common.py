from datetime import date, datetime
from functools import reduce
from operator import attrgetter
from random import sample

import factory
import pytest
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service, Team
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
    random_obj_for_model,
)
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import CommunicationChannel, Interaction
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    EventServiceDeliveryFactory,
)
from datahub.interaction.test.views.utils import resolve_data
from datahub.investment.project.test.factories import InvestmentProjectFactory
from datahub.metadata.models import Service as ServiceModel
from datahub.metadata.test.factories import TeamFactory


class TestAddInteraction(APITestMixin):
    """Tests for the add interaction view."""

    @pytest.mark.parametrize('kind', ('policy_feedback', 'invalid-kind'))
    def test_invalid_kind_is_rejected(self, kind):
        """Test that invalid kind values are rejected."""
        adviser = self.user
        contact = ContactFactory()
        company = contact.company

        data = {
            'kind': kind,
            'company': {
                'id': company.pk,
            },
            'contacts': [{
                'id': contact.pk,
            }],
            'date': '2017-04-18',
            'dit_adviser': {
                'id': adviser.pk,
            },
            'dit_team': {
                'id': adviser.dit_team.pk,
            },
            'service': {
                'id': random_obj_for_model(ServiceModel).pk,
            },
            'subject': 'whatever',
            'was_policy_feedback_provided': False,
        }
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'kind': [f'"{kind}" is not a valid choice.'],
        }

    def test_contacts_copied_to_contact(self):
        """
        Test that the value provided in the contacts field is copied to contact when an
        interaction is created.

        TODO: remove once the contacts field has fully replaced the contact field.
        """
        company = CompanyFactory()
        contacts = ContactFactory.create_batch(2, company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': {
                'id': self.user.pk,
            },
            'company': {
                'id': company.pk,
            },
            'contacts': [{
                'id': contact.pk,
            } for contact in contacts],
            'service': {
                'id': random_obj_for_model(ServiceModel).pk,
            },
            'dit_team': {
                'id': self.user.dit_team.pk,
            },
            'was_policy_feedback_provided': False,
        }

        api_client = self.create_api_client()
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_201_CREATED
        interaction = Interaction.objects.get(pk=response.json()['id'])
        assert interaction.contact == contacts[0]
        assert set(interaction.contacts.all()) == set(contacts)

    def test_error_returned_if_contacts_dont_belong_to_company(self):
        """
        Test that an error is returned if the contacts don't belong to the specified company.
        """
        company = CompanyFactory()
        contacts = [ContactFactory(), ContactFactory(company=company)]
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_adviser': {
                'id': self.user.pk,
            },
            'company': {
                'id': company.pk,
            },
            'contacts': [{
                'id': contact.pk,
            } for contact in contacts],
            'service': {
                'id': random_obj_for_model(ServiceModel).pk,
            },
            'dit_team': {
                'id': self.user.dit_team.pk,
            },
            'was_policy_feedback_provided': False,
        }

        api_client = self.create_api_client()
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': ['The interaction contacts must belong to the specified company.'],
        }


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
        response = self.api_client.patch(
            url,
            data={
                'archived_documents_url_path': 'new_path',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived_documents_url_path'] == 'old_path'

    def test_date_validation(self):
        """Test validation when an invalid date is provided."""
        interaction = CompanyInteractionFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(
            url,
            data={
                'date': 'abcd-de-fe',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data['date'] == [
            'Datetime has wrong format. Use one of these formats instead: YYYY-MM-DD.',
        ]

    def test_contacts_copied_to_contact(self):
        """
        Test that the value provided in the contact field is copied to contacts when an
        interaction is updated.

        TODO: remove once the contacts field has fully replaced the contact field.
        """
        interaction = CompanyInteractionFactory(contacts=[])
        new_contacts = ContactFactory.create_batch(2, company=interaction.company)

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        data = {
            'contacts': [{
                'id': contact.pk,
            } for contact in new_contacts],
        }
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        interaction.refresh_from_db()
        assert interaction.contact == new_contacts[0]
        assert set(interaction.contacts.all()) == set(new_contacts)

    @pytest.mark.parametrize(
        'request_data',
        (
            {
                'company': CompanyFactory,
            },
            {
                'contacts': [ContactFactory],
            },
        ),
    )
    def test_error_returned_if_contacts_dont_belong_to_company(self, request_data):
        """
        Test that an error is returned if an update makes the contacts and company
        fields inconsistent.
        """
        interaction = CompanyInteractionFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        resolved_data = resolve_data(request_data)
        response = self.api_client.patch(url, data=resolved_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': ['The interaction contacts must belong to the specified company.'],
        }

    @pytest.mark.parametrize('include_company', (True, False))
    @pytest.mark.parametrize('include_contacts', (True, False))
    def test_inconsistent_interaction_can_be_updated(self, include_company, include_contacts):
        """
        Test that an interaction with inconsistent company and contact fields can still be
        updated.
        """
        interaction = CompanyInteractionFactory(
            company=CompanyFactory(),
            notes='old notes',
        )

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        data = {'notes': 'new notes'}

        if include_company:
            data['company'] = {'id': interaction.company.pk}

        if include_contacts:
            data['contacts'] = [{'id': contact.pk} for contact in interaction.contacts.all()]

        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['notes'] == data['notes']


class TestListInteractions(APITestMixin):
    """Tests for the list interactions view."""

    def test_filtered_by_company(self):
        """List of interactions filtered by company"""
        company1 = CompanyFactory()
        company2 = CompanyFactory()

        CompanyInteractionFactory.create_batch(3, company=company1)
        interactions = CompanyInteractionFactory.create_batch(2, company=company2)

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, data={'company_id': company2.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}

    def test_filter_by_contact(self):
        """Test filtering interactions by contact (using contacts__id)."""
        contact1 = ContactFactory()
        contact2 = ContactFactory()

        CompanyInteractionFactory.create_batch(3, contacts=[contact1])
        interactions = CompanyInteractionFactory.create_batch(2, contacts=[contact1, contact2])

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(url, data={'contacts__id': contact2.id})

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
            2, investment_project=project,
        )

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(
            url,
            data={
                'investment_project_id': project.id,
            },
        )

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
        response = self.api_client.get(url, data={'event_id': event.id})

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == 3

        actual_ids = {result['id'] for result in response_data['results']}
        expected_ids = {str(service_delivery.id) for service_delivery in service_deliveries}
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'field',
        (
            'company.name',
            'created_on',
            'dit_adviser.first_name',
            'dit_adviser.last_name',
            'subject',
        ),
    )
    def test_sorting(self, field):
        """Test sorting interactions by various fields."""
        data_list = [
            {
                'created_on': datetime(2015, 1, 1),
                'company__name': 'Black Group',
                'dit_adviser__first_name': 'Elaine',
                'dit_adviser__last_name': 'Johnston',
                'subject': 'lorem',
            },
            {
                'created_on': datetime(2005, 4, 1),
                'company__name': 'Hicks Ltd',
                'dit_adviser__first_name': 'Connor',
                'dit_adviser__last_name': 'Webb',
                'subject': 'ipsum',
            },
            {
                'created_on': datetime(2019, 1, 1),
                'company__name': 'Sheppard LLC',
                'dit_adviser__first_name': 'Hayley',
                'dit_adviser__last_name': 'Hunt',
                'subject': 'dolor',
            },
        ]

        interactions = []
        for data in data_list:
            creation_time = data.pop('created_on')
            with freeze_time(creation_time):
                interactions.append(
                    EventServiceDeliveryFactory(**data),
                )

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(
            url,
            data={
                'sortby': field.replace('.', '__'),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(interactions)

        expected = sorted(map(attrgetter(field), interactions))
        if isinstance(expected[0], datetime):
            expected = [format_date_or_datetime(item) for item in expected]

        actual = [
            reduce(  # get nested items if needed
                lambda data, key: data.get(key),
                field.split('.'),
                result,
            )
            for result in response_data['results']
        ]
        assert expected == actual

    def test_sort_by_adviser_first_and_last_name(self):
        """Test sorting interactions by first_name with a secondary last_name sort."""
        people = [
            AdviserFactory(first_name='Alfred', last_name='Jones'),
            AdviserFactory(first_name='Alfred', last_name='Terry'),
            AdviserFactory(first_name='Thomas', last_name='Richards'),
            AdviserFactory(first_name='Thomas', last_name='West'),
        ]
        interactions = EventServiceDeliveryFactory.create_batch(
            len(people),
            **{
                'dit_adviser': factory.Iterator(sample(people, k=len(people))),
            },
        )

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(
            url,
            data={
                'sortby': f'dit_adviser__first_name,dit_adviser__last_name',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == len(interactions)

        actual_ids = [
            interaction['dit_adviser']['id']
            for interaction in response_data['results']
        ]
        expected_ids = [str(person.pk) for person in people]
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'primary_field,secondary_field',
        (
            ('first_name', 'last_name'),
            ('last_name', 'first_name'),
        ),
    )
    def test_sort_by_first_and_last_name_of_first_contact(self, primary_field, secondary_field):
        """Test sorting interactions by the first and last names of the first contact."""
        contacts = [
            ContactFactory(**{primary_field: 'Alfred', secondary_field: 'Jones'}),
            ContactFactory(**{primary_field: 'Alfred', secondary_field: 'Terry'}),
            ContactFactory(**{primary_field: 'Thomas', secondary_field: 'Richards'}),
            ContactFactory(**{primary_field: 'Thomas', secondary_field: 'West'}),
        ]
        interactions = [
            EventServiceDeliveryFactory(contacts=[contact])
            for contact in sample(contacts, len(contacts))
        ]

        url = reverse('api-v3:interaction:collection')
        response = self.api_client.get(
            url,
            data={
                'sortby': f'{primary_field}_of_first_contact,{secondary_field}_of_first_contact',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data['count'] == len(interactions)

        actual_ids = [
            interaction['contacts'][0]['id'] for interaction in response_data['results']
        ]
        expected_ids = [str(person.pk) for person in contacts]
        assert actual_ids == expected_ids


class TestInteractionVersioning(APITestMixin):
    """
    Tests for versions created when interacting with the interaction endpoints.
    """

    def test_add_creates_a_new_version(self):
        """Test that creating an interaction creates a new version."""
        assert Version.objects.count() == 0

        company = CompanyFactory()
        contact = ContactFactory(company=company)
        response = self.api_client.post(
            reverse('api-v3:interaction:collection'),
            data={
                'kind': Interaction.KINDS.interaction,
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_adviser': AdviserFactory().pk,
                'notes': 'hello',
                'company': company.pk,
                'contacts': [contact.pk],
                'service': Service.trade_enquiry.value.id,
                'dit_team': Team.healthcare_uk.value.id,
                'was_policy_feedback_provided': False,
            },
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
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Version.objects.get_for_object(service_delivery).count() == 0
