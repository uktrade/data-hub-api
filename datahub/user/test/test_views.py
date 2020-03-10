import factory
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test.factories import GroupFactory, PermissionFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory, TeamRoleFactory


class TestUserView(APITestMixin):
    """User view test case."""

    def test_who_am_i_authenticated(self):
        """Who am I."""
        permission_names = [
            'view_lorem',
            'view_ipsum',
            'add_cats',
        ]
        content_type = ContentType.objects.first()

        permissions = PermissionFactory.create_batch(
            len(permission_names),
            codename=factory.Iterator(permission_names),
            content_type=content_type,
        )

        group = GroupFactory()
        group.permissions.add(permissions[0])
        role = TeamRoleFactory(name='Test Role')

        team = TeamFactory(name='Test Team', role=role)
        team.role.groups.add(group)

        user_test = create_test_user(dit_team=team)
        user_test.user_permissions.set(permissions[1:])
        api_client = self.create_api_client(user=user_test)

        url = reverse('who_am_i')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        if 'permissions' in response_data:
            response_data['permissions'].sort()

        expected_permissions = [
            f'{content_type.app_label}.add_cats',
            f'{content_type.app_label}.view_ipsum',
            f'{content_type.app_label}.view_lorem',
        ]

        assert response_data == {
            'id': str(user_test.id),
            'name': user_test.name,
            'last_login': None,
            'first_name': user_test.first_name,
            'last_name': user_test.last_name,
            'email': user_test.email,
            'contact_email': user_test.contact_email,
            'telephone_number': user_test.telephone_number,
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
                },
                'disabled_on': None,
            },
            'permissions': expected_permissions,
        }
