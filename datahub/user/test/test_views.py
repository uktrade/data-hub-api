from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test.factories import PermissionFactory, GroupFactory
from datahub.core.test_utils import APITestMixin, get_test_user
from datahub.metadata.test.factories import TeamFactory, TeamRoleFactory


class TestUserView(APITestMixin):
    """User view test case."""

    def test_who_am_i_authenticated(self):
        """Who am I."""
        action = 'read'
        model_name_1 = 'lorem'
        model_name_2 = 'ipsum'

        team_permission = PermissionFactory(codename=f'{action}_{model_name_1}')
        user_permission = PermissionFactory(codename=f'{action}_{model_name_2}')

        group = GroupFactory()
        group.permissions.add(team_permission)

        role = TeamRoleFactory(name='Test Role')

        team = TeamFactory(name='Test Team', role=role)
        team.role.groups.add(group)

        user_test = get_test_user(team=team)
        user_test.user_permissions.add(user_permission)

        url = reverse('who_am_i')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == user_test.name
        assert response.data['first_name'] == user_test.first_name
        assert response.data['id'] == str(user_test.pk)
        assert response.data['team'] == team.name
        assert response.data['team_role'] == role.name
        assert response.data.get('permissions') is not None
        for model in (model_name_1, model_name_2):
            assert action in response.data['permissions'][model]
