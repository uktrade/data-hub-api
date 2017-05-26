from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdvisorFactory, CompanyFactory, ContactFactory
from datahub.core import constants
from datahub.core.test_utils import LeelooTestCase
from datahub.interaction.test.factories import InteractionFactory


class InteractionTestCase(LeelooTestCase):
    """Interaction test case."""

    def test_interaction_detail_view(self):
        """Interaction detail view."""
        interaction = InteractionFactory()
        url = reverse('api-v1:interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(interaction.pk)

    @freeze_time('2017-04-18 13:25:30.986208+00:00')
    def test_add_interaction(self):
        """Test add new interaction."""
        url = reverse('api-v1:interaction-list')
        response = self.api_client.post(url, {
            'interaction_type': constants.InteractionType.business_card.value.id,
            'subject': 'whatever',
            'date': now().isoformat(),
            'dit_advisor': AdvisorFactory().pk,
            'notes': 'hello',
            'company': CompanyFactory().pk,
            'contact': ContactFactory().pk,
            'service': constants.Service.trade_enquiry.value.id,
            'dit_team': constants.Team.healthcare_uk.value.id
        })

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['dit_advisor'] == str(self.user.pk)
        assert response_data['modified_on'] == '2017-04-18T13:25:30.986208'
        assert response_data['created_on'] == '2017-04-18T13:25:30.986208'

    def test_modify_interaction(self):
        """Modify an existing interaction."""
        interaction = InteractionFactory(subject='I am a subject')

        url = reverse('api-v1:interaction-detail', kwargs={'pk': interaction.pk})
        response = self.api_client.patch(url, {
            'subject': 'I am another subject',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subject'] == 'I am another subject'

    def test_list_filtered(self):
        """List of interactions filtered by contact"""
        contact1 = ContactFactory()
        contact2 = ContactFactory()

        InteractionFactory.create_batch(3, contact=contact1)
        interactions = InteractionFactory.create_batch(2, contact=contact2)

        url = '{}?contact_id={}'.format(
            reverse('api-v1:interaction-list'),
            contact2.id
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert {i['id'] for i in response.data['results']} == {str(i.id) for i in interactions}
