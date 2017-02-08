from django.urls import reverse
from rest_framework import status

from datahub.company.test.factories import CompanyFactory
from datahub.core import constants
from datahub.core.test_utils import get_test_user, LeelooTestCase
from datahub.interaction.test.factories import InteractionFactory


class DashboardTestCase(LeelooTestCase):
    """Dashboard test case."""

    def test_intelligent_homepage(self):
        """Intelligent homepage."""
        user = get_test_user()

        # add contact using the API to save the user from the session
        url = reverse('contact-list')
        api_response = self.api_client.post(url, {
            'first_name': 'Oratio',
            'last_name': 'Nelson',
            'title': constants.Title.admiral_of_the_fleet.value.id,
            'company': CompanyFactory().pk,
            'role': constants.Role.owner.value.id,
            'email': 'foo@bar.com',
            'telephone_countrycode': '+44',
            'telephone_number': '123456789',
            'address_same_as_company': True,
            'primary': True
        })
        interaction = InteractionFactory(dit_advisor=user)

        url = reverse('dashboard:intelligent-homepage')
        response = self.api_client.get(url, data={'days': 23})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['contacts']) == 1
        assert response.data['contacts'][0]['id'] == str(api_response.data['id'])
        assert len(response.data['interactions']) == 1
        assert response.data['interactions'][0]['id'] == str(interaction.pk)
