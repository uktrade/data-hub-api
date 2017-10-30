import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory, CompanyFactory, ContactFactory
from datahub.core.test_utils import APITestMixin, get_test_user
from datahub.event.test.factories import EventFactory
from datahub.metadata.models import Team


class TestAdviserPermissions(APITestMixin):
    """User permissions test case."""

    @pytest.mark.parametrize('factory,reverse_url, expected_status',
         (
            (lambda *args: None, 'dashboard:intelligent-homepage', status.HTTP_200_OK),
            (AdviserFactory, 'api-v1:advisor-list', status.HTTP_200_OK),
            (CompanyFactory, 'api-v3:company:collection', status.HTTP_200_OK),
            (ContactFactory, 'api-v3:contact:list', status.HTTP_200_OK),
            (EventFactory, 'api-v3:event:collection', status.HTTP_403_FORBIDDEN)
         ))
    def test_adviser_list_view(self, factory, reverse_url, expected_status):
        """User different permissions for LEP team role user."""
        team = Team.objects.filter(role__team_role_groups__name='LEP').first()
        self._user = get_test_user(team=team)

        url = reverse(reverse_url)
        factory()

        response = self.api_client.get(url)
        assert response.status_code == expected_status
