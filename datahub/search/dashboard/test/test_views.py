from datetime import datetime

from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import ContactFactory
from datahub.core.test_utils import APITestMixin
from datahub.interaction.test.factories import CompanyInteractionFactory


class TestDashboard(APITestMixin):
    """Dashboard test case."""

    def test_intelligent_homepage(self, setup_es):
        """Intelligent homepage."""
        datetimes = [datetime(year, 1, 1) for year in range(2015, 2030)]
        interactions = []
        contacts = []

        for creation_datetime in datetimes:
            with freeze_time(creation_datetime):
                interactions.append(CompanyInteractionFactory(dit_adviser=self.user))
                contacts.append(ContactFactory(created_by=self.user))

        setup_es.indices.refresh()

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        resp_contacts = response_data['contacts']

        resp_contact_ids = [contact['id'] for contact in resp_contacts]
        assert resp_contact_ids == [str(contact.id) for contact in contacts[:-6:-1]]

        resp_interactions = response_data['interactions']
        resp_interaction_ids = [interaction['id'] for interaction in resp_interactions]

        assert resp_interaction_ids == [
            str(interaction.id) for interaction in interactions[:-6:-1]
        ]

        resp_interaction = response.data['interactions'][0]
        assert isinstance(resp_interaction['company'], dict)
        assert resp_interaction['company']['name'] == interactions[-1].company.name

    def test_intelligent_homepage_limit(self, setup_es):
        """Test the limit param."""
        CompanyInteractionFactory.create_batch(15, dit_adviser=self.user)
        ContactFactory.create_batch(15, created_by=self.user)

        setup_es.indices.refresh()

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(url, data={
            'limit': 10
        })

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['contacts']) == 10
        assert len(response_data['interactions']) == 10
