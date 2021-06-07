from datetime import date, datetime
from functools import partial, reduce
from operator import attrgetter
from random import sample

import pytest
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from reversion.models import Version

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.constants import Service
from datahub.core.reversion import EXCLUDED_BASE_MODEL_FIELDS
from datahub.core.test_utils import (
    APITestMixin,
    create_test_user,
    format_date_or_datetime,
    random_obj_for_model,
)
from datahub.event.test.factories import EventFactory
from datahub.interaction.models import CommunicationChannel, Interaction, InteractionPermission
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    EventServiceDeliveryFactory,
    InteractionDITParticipantFactory,
)
from datahub.interaction.test.permissions import (
    NON_RESTRICTED_CHANGE_PERMISSIONS,
)
from datahub.interaction.test.utils import random_service
from datahub.interaction.test.views.utils import resolve_data
from datahub.investment.project.test.factories import InvestmentProjectFactory
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
            'dit_participants': [
                {
                    'adviser': {
                        'id': adviser.pk,
                    },
                },
            ],
            'service': {
                'id': random_service().pk,
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

    @pytest.mark.parametrize(
        'data,errors',
        (
            # empty string not allowed for theme
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],

                    'theme': '',
                },
                {
                    'theme': ['"" is not a valid choice.'],
                },
            ),

            # invalid theme not allowed
            (
                {
                    'kind': Interaction.Kind.INTERACTION,
                    'communication_channel': partial(random_obj_for_model, CommunicationChannel),
                    'date': date.today().isoformat(),
                    'subject': 'whatever',
                    'service': Service.inbound_referral.value.id,
                    'was_policy_feedback_provided': False,
                    'dit_participants': [
                        {'adviser': AdviserFactory},
                    ],

                    'theme': 'not_valid',
                },
                {
                    'theme': ['"not_valid" is not a valid choice.'],
                },
            ),
        ),
    )
    def test_validation(self, data, errors):
        """Test validation errors."""
        company = CompanyFactory()
        resolved_data = {
            'company': company.pk,
            'contacts': [ContactFactory(company=company).pk],
            **resolve_data(data),
        }
        url = reverse('api-v3:interaction:collection')
        response = self.api_client.post(url, resolved_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors

    def test_error_returned_if_contacts_dont_belong_to_company(self):
        """
        Test that an error is returned if the contacts don't belong to the specified company.
        """
        company = CompanyFactory()
        contacts = [ContactFactory(), ContactFactory(company=company)]
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {'adviser': self.user.pk},
            ],
            'company': {
                'id': company.pk,
            },
            'contacts': [{
                'id': contact.pk,
            } for contact in contacts],
            'service': {
                'id': random_service().pk,
            },
            'was_policy_feedback_provided': False,
        }

        api_client = self.create_api_client()
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {
            'non_field_errors': ['The interaction contacts must belong to the specified company.'],
        }

    def test_multiple_participating_advisers_can_be_specified(self):
        """Test that an interaction can be created with multiple DIT participants."""
        contact = ContactFactory()
        communication_channel = random_obj_for_model(CommunicationChannel)
        advisers = AdviserFactory.create_batch(5)
        advisers.sort(key=attrgetter('pk'))

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {
                    'adviser': {
                        'id': adviser.pk,
                    },
                }
                for adviser in advisers
            ],
            'company': {
                'id': contact.company.pk,
            },
            'contacts': [{
                'id': contact.pk,
            }],
            'service': {
                'id': random_service().pk,
            },
            'was_policy_feedback_provided': False,
        }

        api_client = self.create_api_client()
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        response_data['dit_participants'].sort(
            key=lambda dit_participant: dit_participant['adviser']['id'],
        )
        assert response_data['dit_participants'] == [
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
            }
            for adviser in advisers
        ]

    def test_error_returned_if_duplicate_participating_advisers_specified(self):
        """
        Test that an error is returned if an adviser is specified as a DIT participant
        multiple times.
        """
        contact = ContactFactory()
        communication_channel = random_obj_for_model(CommunicationChannel)
        dit_adviser = AdviserFactory()

        url = reverse('api-v3:interaction:collection')
        request_data = {
            'kind': Interaction.Kind.INTERACTION,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date': date.today().isoformat(),
            'dit_participants': [
                {
                    'adviser': {
                        'id': dit_adviser.pk,
                    },
                },
                {
                    'adviser': {
                        'id': AdviserFactory().pk,
                    },
                },
                {
                    'adviser': {
                        'id': dit_adviser.pk,
                    },
                },
            ],
            'company': {
                'id': contact.company.pk,
            },
            'contacts': [{
                'id': contact.pk,
            }],
            'service': {
                'id': random_service().pk,
            },
            'was_policy_feedback_provided': False,
        }

        api_client = self.create_api_client()
        response = api_client.post(url, request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # An error should be returned for each duplicated item in the dit_participants list in
        # the request
        assert response.json() == {
            'dit_participants': [
                {'adviser': ['You cannot add the same adviser more than once.']},
                {},
                {'adviser': ['You cannot add the same adviser more than once.']},
            ],
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
            archived=False,
            archived_by=None,
            archived_on=None,
            archived_reason=None,
        )

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        # TODO: also test `archived` field once we have made it read-only
        response = self.api_client.patch(
            url,
            data={
                'archived_documents_url_path': 'new_path',
                'archived': True,
                'archived_by': 123,
                'archived_on': date.today(),
                'archived_reason': 'test',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['archived_documents_url_path'] == 'old_path'
        assert response.data['archived'] is False
        assert response.data['archived_by'] is None
        assert response.data['archived_on'] is None
        assert response.data['archived_reason'] is None

    @pytest.mark.parametrize(
        'data,errors',
        (
            # empty string not allowed for theme
            (
                {
                    'theme': '',
                },
                {
                    'theme': ['"" is not a valid choice.'],
                },
            ),

            # invalid theme not allowed
            (
                {
                    'theme': 'not_valid',
                },
                {
                    'theme': ['"not_valid" is not a valid choice.'],
                },
            ),

            # date validation
            (
                {
                    'date': 'abcd-de-fe',
                },
                {
                    'date': [
                        'Datetime has wrong format. Use one of these formats instead: YYYY-MM-DD.',
                    ],
                },
            ),

            # cannot remove all participants
            (
                {
                    'dit_participants': [],
                },
                {
                    'dit_participants': {
                        'non_field_errors': ['This list may not be empty.'],
                    },
                },
            ),
        ),
    )
    def test_validation(self, data, errors):
        """Test validation when an invalid date is provided."""
        interaction = CompanyInteractionFactory()

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == errors

    @pytest.mark.parametrize(
        'request_data',
        (
            {
                'company': CompanyFactory,
            },
            {
                'companies': [CompanyFactory],
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

    def test_can_replace_some_participants(self):
        """Test that a subset of existing DIT participants can be replaced."""
        interaction = CompanyInteractionFactory(dit_participants=[])
        dit_participants = InteractionDITParticipantFactory.create_batch(
            3,
            interaction=interaction,
        )
        # Change the first adviser's team so that we can check that the participant's team is
        # unchanged after the update.
        dit_participants[0].adviser.dit_team = TeamFactory()
        dit_participants[0].adviser.save()

        new_advisers = [
            dit_participants[0].adviser,
            AdviserFactory(),
        ]

        request_data = {
            'dit_participants': [
                {
                    'adviser': {
                        'id': adviser.pk,
                    },
                }
                for adviser in new_advisers
            ],
        }

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, data=request_data)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        response_data['dit_participants'].sort(
            key=lambda dit_participant: dit_participant['adviser']['id'],
        )

        expected_advisers_and_teams = [
            (new_advisers[0], dit_participants[0].team),
            (new_advisers[1], new_advisers[1].dit_team),
        ]
        expected_advisers_and_teams.sort(key=lambda adviser_and_team: adviser_and_team[0].pk)

        assert response_data['dit_participants'] == [
            {
                'adviser': {
                    'id': str(adviser.pk),
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                    'name': adviser.name,
                },
                'team': {
                    'id': str(team.pk),
                    'name': team.name,
                },
            }
            for adviser, team in expected_advisers_and_teams
        ]

    def test_can_replace_all_participants(self):
        """Test that all existing participants can be replaced with different ones."""
        interaction = CompanyInteractionFactory(dit_participants=[])
        InteractionDITParticipantFactory.create_batch(
            3,
            interaction=interaction,
        )

        new_advisers = AdviserFactory.create_batch(2)
        new_advisers.sort(key=attrgetter('pk'))

        request_data = {
            'dit_participants': [
                {
                    'adviser': {
                        'id': adviser.pk,
                    },
                }
                for adviser in new_advisers
            ],
        }

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, data=request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        response_data['dit_participants'].sort(
            key=lambda dit_participant: dit_participant['adviser']['id'],
        )

        expected_advisers_and_teams = [(adviser, adviser.dit_team) for adviser in new_advisers]

        assert response_data['dit_participants'] == [
            {
                'adviser': {
                    'id': str(adviser.pk),
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                    'name': adviser.name,
                },
                'team': {
                    'id': str(team.pk),
                    'name': team.name,
                },
            }
            for adviser, team in expected_advisers_and_teams
        ]

    def test_can_add_participants(self):
        """Test that participants can be added to an interaction without any being removed."""
        interaction = CompanyInteractionFactory(dit_participants=[])
        dit_participants = InteractionDITParticipantFactory.create_batch(
            3,
            interaction=interaction,
        )

        new_advisers = [
            *[dit_participant.adviser for dit_participant in dit_participants],
            *AdviserFactory.create_batch(2),
        ]
        new_advisers.sort(key=attrgetter('pk'))

        request_data = {
            'dit_participants': [
                {
                    'adviser': {
                        'id': adviser.pk,
                    },
                }
                for adviser in new_advisers
            ],
        }

        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, data=request_data)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        response_data['dit_participants'].sort(
            key=lambda dit_participant: dit_participant['adviser']['id'],
        )

        expected_advisers_and_teams = [(adviser, adviser.dit_team) for adviser in new_advisers]

        assert response_data['dit_participants'] == [
            {
                'adviser': {
                    'id': str(adviser.pk),
                    'first_name': adviser.first_name,
                    'last_name': adviser.last_name,
                    'name': adviser.name,
                },
                'team': {
                    'id': str(team.pk),
                    'name': team.name,
                },
            }
            for adviser, team in expected_advisers_and_teams
        ]

    @pytest.mark.parametrize(
        'current_status,new_status',
        (
            (Interaction.Status.DRAFT, Interaction.Status.DRAFT),
            (Interaction.Status.DRAFT, Interaction.Status.COMPLETE),
            (Interaction.Status.COMPLETE, Interaction.Status.COMPLETE),
        ),
    )
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_status_change_valid(self, current_status, new_status):
        """
        Test the different ways that an Interaction's status can change.
        """
        interaction = CompanyInteractionFactory(status=current_status)
        api_client = self.create_api_client()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'status': new_status,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == new_status

    @pytest.mark.parametrize(
        'current_status,new_status,response_body',
        (
            (
                Interaction.Status.DRAFT,
                None,
                {'status': ['This field may not be null.']},
            ),
            (
                Interaction.Status.COMPLETE,
                Interaction.Status.DRAFT,
                {'non_field_errors': ['The status of a complete interaction cannot change.']},
            ),
            (
                Interaction.Status.COMPLETE,
                None,
                {'status': ['This field may not be null.']},
            ),
        ),
    )
    @freeze_time('2017-04-18 13:25:30.986208')
    def test_status_change_invalid(self, current_status, new_status, response_body):
        """
        Test the different ways that an Interaction's status can change.
        """
        interaction = CompanyInteractionFactory(status=current_status)
        api_client = self.create_api_client()
        url = reverse('api-v3:interaction:item', kwargs={'pk': interaction.pk})
        response = api_client.patch(
            url,
            data={
                'status': new_status,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == response_body


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

        CompanyInteractionFactory.create_batch(3, contacts=[contact])
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

        CompanyInteractionFactory.create_batch(3, contacts=[contact])
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
            'subject',
        ),
    )
    def test_sorting(self, field):
        """Test sorting interactions by various fields."""
        data_list = [
            {
                'created_on': datetime(2015, 1, 1),
                'company__name': 'Black Group',
                'subject': 'lorem',
            },
            {
                'created_on': datetime(2005, 4, 1),
                'company__name': 'Hicks Ltd',
                'subject': 'ipsum',
            },
            {
                'created_on': datetime(2019, 1, 1),
                'company__name': 'Sheppard LLC',
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
                'kind': Interaction.Kind.INTERACTION,
                'communication_channel': random_obj_for_model(CommunicationChannel).pk,
                'subject': 'whatever',
                'date': date.today().isoformat(),
                'dit_participants': [
                    {'adviser': AdviserFactory().pk},
                ],
                'notes': 'hello',
                'company': company.pk,
                'contacts': [contact.pk],
                'service': Service.inbound_referral.value.id,
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
                'kind': Interaction.Kind.INTERACTION,
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


class TestArchiveViews(APITestMixin):
    """
    Tests for the archive and unarchive views.
    """

    @pytest.mark.parametrize(
        'permissions', NON_RESTRICTED_CHANGE_PERMISSIONS,
    )
    def test_archive_interaction_non_restricted_user(self, permissions):
        """
        Tests archiving an interaction for a non-restricted user.
        """
        requester = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=requester)

        interaction = CompanyInteractionFactory()
        url = reverse(
            'api-v3:interaction:archive-item',
            kwargs={'pk': interaction.pk},
        )
        response = api_client.post(
            url,
            data={
                'reason': 'archive reason',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is True
        assert response_data['archived_by']['id'] == str(requester.pk)
        assert response_data['archived_reason'] == 'archive reason'

    def test_archive_interaction_restricted_user_associated_project(self):
        """
        Tests archiving an interaction for a restricted user.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject],
            dit_team=project_creator.dit_team,  # same dit team as the project creator
        )
        api_client = self.create_api_client(user=requester)
        interaction = CompanyInteractionFactory(investment_project=project)
        url = reverse(
            'api-v3:interaction:archive-item',
            kwargs={'pk': interaction.pk},
        )
        response = api_client.post(
            url,
            data={
                'reason': 'archive reason',
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is True
        assert response_data['archived_by']['id'] == str(requester.pk)
        assert response_data['archived_reason'] == 'archive reason'

    def test_archive_interaction_restricted_user_non_associated_project(self):
        """
        Test that a restricted user cannot archive a non-associated interaction.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        # Ensure the requester is created for a different DIT team
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject],
        )
        api_client = self.create_api_client(user=requester)
        interaction = CompanyInteractionFactory(investment_project=project)
        url = reverse(
            'api-v3:interaction:archive-item',
            kwargs={'pk': interaction.pk},
        )
        response = api_client.post(
            url,
            data={
                'reason': 'archive reason',
            },
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'data,response_data',
        (
            (
                {},
                {'reason': ['This field is required.']},
            ),
            (
                {'reason': ''},
                {'reason': ['This field may not be blank.']},
            ),
            (
                {'reason': None},
                {'reason': ['This field may not be null.']},
            ),
        ),
    )
    def test_archive_failures(self, data, response_data):
        """
        Test archive an interaction without providing a reason.
        """
        interaction = CompanyInteractionFactory()
        url = reverse(
            'api-v3:interaction:archive-item',
            kwargs={'pk': interaction.pk},
        )
        response = self.api_client.post(url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == response_data

    @pytest.mark.parametrize(
        'permissions', NON_RESTRICTED_CHANGE_PERMISSIONS,
    )
    def test_unarchive_interaction_non_restricted_user(self, permissions):
        """
        Tests un-archiving an interaction for a non-restricted user.
        """
        requester = create_test_user(permission_codenames=permissions)
        api_client = self.create_api_client(user=requester)

        interaction = CompanyInteractionFactory(
            archived=True,
            archived_by=requester,
            archived_reason='just cos',
            archived_on=now(),
        )
        url = reverse(
            'api-v3:interaction:unarchive-item',
            kwargs={'pk': interaction.pk},
        )
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is False
        assert response_data['archived_by'] is None
        assert response_data['archived_reason'] == ''
        assert response_data['archived_on'] is None

    def test_unarchive_interaction_restricted_user_associated_project(self):
        """
        Tests archiving an interaction for a restricted user.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject],
            dit_team=project_creator.dit_team,  # same dit team as the project creator
        )
        api_client = self.create_api_client(user=requester)
        interaction = CompanyInteractionFactory(
            investment_project=project,
            archived=True,
            archived_by=project_creator,
            archived_on=now(),
            archived_reason='why not',
        )
        url = reverse(
            'api-v3:interaction:unarchive-item',
            kwargs={'pk': interaction.pk},
        )
        response = api_client.post(
            url,
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['archived'] is False
        assert response_data['archived_by'] is None
        assert response_data['archived_reason'] == ''
        assert response_data['archived_on'] is None

    def test_unarchive_interaction_restricted_user_non_associated_project(self):
        """
        Test that a restricted user cannot un-archive a non-associated interaction.
        """
        project_creator = AdviserFactory()
        project = InvestmentProjectFactory(created_by=project_creator)
        # Ensure the requester is created for a different DIT team
        requester = create_test_user(
            permission_codenames=[InteractionPermission.change_associated_investmentproject],
        )
        api_client = self.create_api_client(user=requester)
        interaction = CompanyInteractionFactory(
            investment_project=project,
            archived=True,
            archived_by=project_creator,
            archived_on=now(),
            archived_reason='why not',
        )
        url = reverse(
            'api-v3:interaction:unarchive-item',
            kwargs={'pk': interaction.pk},
        )
        response = api_client.post(
            url,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
