from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test.factories import PermissionFactory
from datahub.core.test_utils import APITestMixin, get_test_user
from datahub.metadata.test.factories import TeamFactory


class TestUserView(APITestMixin):
    """User view test case."""

    def test_who_am_i_authenticated(self):
        """Who am I."""
        team_permission = PermissionFactory()
        user_permission = PermissionFactory()

        team = TeamFactory()
        team.role.team_role_permissions.add(team_permission)

        user_test = get_test_user()
        user_test.permissions.add(user_permission)

        url = reverse('who_am_i')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == user_test.name
        assert response.data['first_name'] == user_test.first_name
        assert response.data['id'] == str(user_test.pk)
