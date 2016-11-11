from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from company.test.factories import CompanyFactory, ContactFactory, InteractionFactory
from core.test_utils import LeelooTestCase, get_test_user


class DashboardTestCase(LeelooTestCase):

    def test_intelligent_homepage(self):

        user = get_test_user()
        contact = ContactFactory(advisor=user.advisor)
        interaction = InteractionFactory(dit_advisor=user.advisor)

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(url, data={'days': 23})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['contacts']) == 1
        assert response.data['contacts'][0]['id'] == str(contact.pk)
        assert len(response.data['interactions']) == 1
        assert response.data['interactions'][0]['id'] == str(interaction.pk)
