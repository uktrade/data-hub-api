from datetime import datetime

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.interaction.models import InteractionPermission
from datahub.interaction.test.factories import (
    CompanyInteractionFactory,
    InteractionDITParticipantFactory,
)


class TestDashboard(APITestMixin):
    """Dashboard test case."""

    def test_intelligent_homepage(self, es_with_collector):
        """Intelligent homepage."""
        datetimes = [datetime(year, 1, 1) for year in range(2015, 2030)]
        interactions = []
        contacts = []

        for creation_datetime in datetimes:
            with freeze_time(creation_datetime):
                interaction = CompanyInteractionFactory(dit_participants=[])
                InteractionDITParticipantFactory(interaction=interaction)
                InteractionDITParticipantFactory(interaction=interaction, adviser=self.user)
                interactions.append(interaction)
                contacts.append(ContactFactory(created_by=self.user))

        es_with_collector.flush_and_refresh()

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        actual_contacts = response_data['contacts']

        actual_contact_ids = [contact['id'] for contact in actual_contacts]
        # Latest 5 contacts, most recent first
        expected_contact_ids = [str(contact.id) for contact in contacts[:-6:-1]]
        assert actual_contact_ids == expected_contact_ids

        actual_interactions = response_data['interactions']
        actual_interaction_ids = [interaction['id'] for interaction in actual_interactions]

        # Latest 5 interactions, most recent first
        expected_interaction_ids = [
            str(interaction.id) for interaction in interactions[:-6:-1]
        ]
        assert actual_interaction_ids == expected_interaction_ids

        actual_first_interaction = response.data['interactions'][0]
        assert isinstance(actual_first_interaction['company'], dict)
        assert actual_first_interaction['company']['name'] == interactions[-1].company.name

    def test_intelligent_homepage_limit(self, es_with_collector):
        """Test the limit param."""
        CompanyInteractionFactory.create_batch(15, dit_participants__adviser=self.user)
        ContactFactory.create_batch(15, created_by=self.user)

        es_with_collector.flush_and_refresh()

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(
            url,
            data={
                'limit': 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['contacts']) == 10
        assert len(response_data['interactions']) == 10

    def test_contact_permission(self, es_with_collector):
        """Test that the contact view permission is enforced."""
        requester = create_test_user(
            permission_codenames=(InteractionPermission.view_all,),
        )
        CompanyInteractionFactory.create_batch(5, dit_participants__adviser=requester)
        ContactFactory.create_batch(5, created_by=requester)

        es_with_collector.flush_and_refresh()

        api_client = self.create_api_client(user=requester)

        url = reverse('dashboard:intelligent-homepage')
        response = api_client.get(
            url,
            data={
                'limit': 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['contacts'] == []
        assert len(response_data['interactions']) == 5

    def test_interaction_permission(self, es_with_collector):
        """Test that the interaction view permission is enforced."""
        requester = create_test_user(
            permission_codenames=('view_contact',),
        )
        InteractionDITParticipantFactory.create_batch(5, adviser=requester)
        ContactFactory.create_batch(5, created_by=requester)

        es_with_collector.flush_and_refresh()

        api_client = self.create_api_client(user=requester)

        url = reverse('dashboard:intelligent-homepage')
        response = api_client.get(
            url,
            data={
                'limit': 10,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['contacts']) == 5
        assert response_data['interactions'] == []
