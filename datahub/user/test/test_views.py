import factory
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test.factories import GroupFactory, PermissionFactory
from datahub.core.test_utils import APITestMixin, get_test_user
from datahub.metadata.test.factories import TeamFactory, TeamRoleFactory


class TestUserView(APITestMixin):
    """User view test case."""

    def test_who_am_i_authenticated(self):
        """Who am I."""
        permissions = [
            'read_lorem',
            'read_ipsum',
            'add_cats',
        ]
        content_type = ContentType.objects.first()

        team_permission = PermissionFactory(
            codename=permissions[0],
            content_type=content_type
        )
        user_permissions = PermissionFactory.create_batch(
            2,
            codename=factory.Iterator(permissions[1:]),
            content_type=content_type
        )

        group = GroupFactory()
        group.permissions.add(team_permission)

        role = TeamRoleFactory(name='Test Role')

        team = TeamFactory(name='Test Team', role=role)
        team.role.groups.add(group)

        user_test = get_test_user(team=team)
        user_test.user_permissions.set(user_permissions)

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
                'name': 'Test Team',
                'role': {
                    'id': str(role.id),
                    'name': 'Test Role',
                },
                'uk_region': {
                    'id': str(team.uk_region_id),
                    'name': 'East Midlands',
                },
                'country': {
                    'id': str(team.country_id),
                    'name': 'France',
                }
            },
            'permissions': [
                f'{content_type.app_label}.{permission}' for permission in permissions
            ]
        }
