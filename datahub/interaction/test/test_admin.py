from uuid import uuid4

import pytest
from django.contrib.admin import site
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import CompanyFactory, ContactFactory
from datahub.core.admin import get_change_url
from datahub.core.test_utils import AdminTestMixin, random_obj_for_model
from datahub.interaction.admin import InteractionAdmin
from datahub.interaction.models import CommunicationChannel, Interaction
from datahub.interaction.test.factories import CompanyInteractionFactory
from datahub.metadata.models import Service, Team


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
