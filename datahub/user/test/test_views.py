from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test.factories import GroupFactory, PermissionFactory
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
        assert response.json() == {
            'id': str(user_test.id),
            'name': user_test.name,
            'last_login': None,
            'first_name': user_test.first_name,
            'last_name': user_test.last_name,
            'email': user_test.email,
            'contact_email': '',
            'telephone_number': '',
            'dit_team': {
                'id': str(team.id),
                'disabled_on': None,
                'name': 'Test Team',
                'role': {
                    'id': str(role.id),
                    'disabled_on': None,
                    'name': 'Test Role',
                    'groups': [group.id],
                },
                'uk_region': {
                    'id': str(team.uk_region_id),
                    'disabled_on': None,
                    'name': 'East Midlands',
                },
                'country': {
                    'id': str(team.country_id),
                    'disabled_on': None,
                    'name': 'France',
                }
            },
            'permissions': {
                model_name_1: [action],
                model_name_2: [action],
            }}
