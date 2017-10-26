from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.metadata.models import Team
from datahub.core.test_utils import APITestMixin, get_test_user
from datahub.event.test.factories import EventFactory


class TestAdviserPermissions(APITestMixin):
    """User permissions test case."""

    def test_adviser_list_view(self):
        team = Team.objects.filter(role__team_role_groups__name='LEP').first()
        self._user = get_test_user(team=team)

        url_dashboard = reverse('dashboard:intelligent-homepage')
        AdviserFactory()
        url_adviser_list = reverse('api-v1:advisor-list')
        CompanyFactory()
        CompanyFactory()
        url_companies = reverse('api-v3:company:collection')
        ContactFactory()
        url_contacts = reverse('api-v3:contact:list')
        EventFactory()
        url_events = reverse('api-v3:event:collection')

        response = self.api_client.get(url_adviser_list)
        assert response.status_code == status.HTTP_200_OK

        response = self.api_client.get(url_companies)
        assert response.status_code == status.HTTP_200_OK

        response = self.api_client.get(url_contacts)
        assert response.status_code == status.HTTP_200_OK

        response = self.api_client.get(url_events)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        response = self.api_client.get(url_dashboard)
        assert response.status_code == status.HTTP_200_OK


