from uuid import uuid4

import pytest
from django.contrib.admin import site
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.admin import get_change_url
from datahub.core.test_utils import AdminTestMixin, random_obj_for_model
from datahub.interaction.admin import InteractionAdmin
from datahub.interaction.models import CommunicationChannel, Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.metadata.models import Service, Team
from datahub.metadata.test.factories import TeamFactory


class TestInteractionAdminContacts(AdminTestMixin):
    """
    Tests for the contacts and contact logic in interaction admin.

    TODO: The app and update tests will be removed once the migration from contact to
     contacts is complete.
    """

    def test_add(self):
        """Test that adding an interaction also sets the contact field."""
        company = CompanyFactory()
        contacts = ContactFactory.create_batch(2, company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse(admin_urlname(Interaction._meta, 'add'))
        data = {
            'id': uuid4(),
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date_0': '2018-01-01',
            'date_1': '00:00:00',
            'dit_adviser': self.user.pk,
            'company': company.pk,
            'contacts': [contact.pk for contact in contacts],
            'service': random_obj_for_model(Service).pk,
            'dit_team': random_obj_for_model(Team).pk,
            'was_policy_feedback_provided': False,
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        assert Interaction.objects.count() == 1
        interaction = Interaction.objects.first()

        assert interaction.contact == contacts[0]
        assert set(interaction.contacts.all()) == set(contacts)

    def test_update_contact_to_non_null(self):
        """
        Test that updating an interaction with a value in contacts also sets the contact field.
        """
        interaction = CompanyInteractionFactory()
        new_contacts = ContactFactory.create_batch(2, company=interaction.company)

        url = get_change_url(interaction)
        data = {
            # Unchanged values
            'id': interaction.pk,
            'kind': Interaction.KINDS.interaction,
            'communication_channel': interaction.communication_channel.pk,
            'subject': interaction.subject,
            'date_0': interaction.date.date().isoformat(),
            'date_1': interaction.date.time().isoformat(),
            'dit_adviser': interaction.dit_adviser.pk,
            'company': interaction.company.pk,
            'service': interaction.service.pk,
            'dit_team': interaction.dit_team.pk,
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'policy_feedback_notes': interaction.policy_feedback_notes,
            'policy_areas': [],
            'policy_issue_types': [],
            'event': '',

            # Changed values
            'contacts': [contact.pk for contact in new_contacts],
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        interaction.refresh_from_db()
        assert interaction.contact == new_contacts[0]
        assert set(interaction.contacts.all()) == set(new_contacts)

    def test_update_contact_to_null(self):
        """Test that removing all contacts from an interaction clears the contact field."""
        interaction = CompanyInteractionFactory()

        url = get_change_url(interaction)
        data = {
            # Unchanged values
            'id': interaction.pk,
            'kind': Interaction.KINDS.interaction,
            'communication_channel': interaction.communication_channel.pk,
            'subject': interaction.subject,
            'date_0': interaction.date.date().isoformat(),
            'date_1': interaction.date.time().isoformat(),
            'dit_adviser': interaction.dit_adviser.pk,
            'company': interaction.company.pk,
            'service': interaction.service.pk,
            'dit_team': interaction.dit_team.pk,
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'policy_feedback_notes': interaction.policy_feedback_notes,
            'policy_areas': [],
            'policy_issue_types': [],
            'event': '',

            # Changed values
            'contacts': [],
        }
        response = self.client.post(url, data=data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        interaction.refresh_from_db()
        assert interaction.contact is None
        assert interaction.contacts.count() == 0

    @pytest.mark.parametrize(
        'num_contacts,expected_display_value',
        (
            (0, ''),
            (1, '{first_contact_name}'),
            (2, '{first_contact_name} and 1 more'),
            (10, '{first_contact_name} and 9 more'),
        ),
    )
    def test_get_contact_names(self, num_contacts, expected_display_value):
        """Test that contact names are formatted as expected."""
        interaction = CompanyInteractionFactory(
            contacts=ContactFactory.create_batch(num_contacts),
        )
        interaction_admin = InteractionAdmin(Interaction, site)
        first_contact = interaction.contacts.order_by('pk').first()
        formatted_expected_display_value = expected_display_value.format(
            first_contact_name=first_contact.name if first_contact else '',
        )
        assert interaction_admin.get_contact_names(interaction) == formatted_expected_display_value


class TestInteractionAdminParticipants(AdminTestMixin):
    """
    Tests for the dit_adviser, dit_team and dit_participants logic in interaction admin.

    TODO: These tests will be removed once the migration from dit_adviser and dit_team to
     dit_participants is complete.
    """

    def test_add(self):
        """Test that adding an interaction also creates a DIT participant."""
        company = CompanyFactory()
        contacts = ContactFactory.create_batch(2, company=company)
        communication_channel = random_obj_for_model(CommunicationChannel)

        url = reverse(admin_urlname(Interaction._meta, 'add'))
        dit_adviser = AdviserFactory()
        dit_team = TeamFactory()

        data = {
            'id': uuid4(),
            'kind': Interaction.KINDS.interaction,
            'communication_channel': communication_channel.pk,
            'subject': 'whatever',
            'date_0': '2018-01-01',
            'date_1': '00:00:00',
            'dit_adviser': dit_adviser.pk,
            'company': company.pk,
            'contacts': [contact.pk for contact in contacts],
            'service': random_obj_for_model(Service).pk,
            'dit_team': dit_team.pk,
            'was_policy_feedback_provided': False,
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        assert Interaction.objects.count() == 1
        interaction = Interaction.objects.first()

        assert interaction.dit_participants.count() == 1

        dit_participant = interaction.dit_participants.first()

        assert dit_participant.adviser == dit_adviser
        assert dit_participant.team == dit_team

    def test_update_without_existing_participant(self):
        """
        Test that if an interaction without an existing DIT participant is updated, a
        DIT participant is created.
        """
        interaction = CompanyInteractionFactory(dit_participants=[])
        new_dit_adviser = AdviserFactory()
        new_dit_team = TeamFactory()

        url = get_change_url(interaction)
        data = {
            # Unchanged values
            'id': interaction.pk,
            'kind': Interaction.KINDS.interaction,
            'communication_channel': interaction.communication_channel.pk,
            'subject': interaction.subject,
            'date_0': interaction.date.date().isoformat(),
            'date_1': interaction.date.time().isoformat(),
            'company': interaction.company.pk,
            'service': interaction.service.pk,
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'policy_feedback_notes': interaction.policy_feedback_notes,
            'policy_areas': [],
            'policy_issue_types': [],
            'event': '',

            # Changed values
            'dit_adviser': new_dit_adviser.pk,
            'dit_team': new_dit_team.pk,
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        interaction.refresh_from_db()
        assert interaction.dit_participants.count() == 1

        dit_participant = interaction.dit_participants.first()
        assert dit_participant.adviser == new_dit_adviser
        assert dit_participant.team == new_dit_team

    @pytest.mark.parametrize('update_dit_adviser', (True, False))
    @pytest.mark.parametrize('update_dit_team', (True, False))
    def test_update_with_existing_participant(self, update_dit_adviser, update_dit_team):
        """
        Test that if an interaction with an existing DIT participant is updated the participant
        is updated as well.
        """
        interaction = CompanyInteractionFactory()

        new_dit_adviser = AdviserFactory() if update_dit_adviser else interaction.dit_adviser
        new_dit_team = TeamFactory() if update_dit_team else interaction.dit_team

        url = get_change_url(interaction)
        data = {
            # Unchanged values
            'id': interaction.pk,
            'kind': Interaction.KINDS.interaction,
            'communication_channel': interaction.communication_channel.pk,
            'subject': interaction.subject,
            'date_0': interaction.date.date().isoformat(),
            'date_1': interaction.date.time().isoformat(),
            'company': interaction.company.pk,
            'service': interaction.service.pk,
            'was_policy_feedback_provided': interaction.was_policy_feedback_provided,
            'policy_feedback_notes': interaction.policy_feedback_notes,
            'policy_areas': [],
            'policy_issue_types': [],
            'event': '',

            # Possibly changed values
            'dit_adviser': new_dit_adviser.pk,
            'dit_team': new_dit_team.pk,
        }
        response = self.client.post(url, data, follow=True)

        assert response.status_code == status.HTTP_200_OK

        interaction.refresh_from_db()
        assert interaction.dit_participants.count() == 1

        dit_participant = interaction.dit_participants.first()

        assert dit_participant.adviser == new_dit_adviser
        assert dit_participant.team == new_dit_team
