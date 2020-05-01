from django.contrib.auth.models import Permission
from rest_framework import status
from rest_framework.test import APIRequestFactory

from datahub.core.test.factories import GroupFactory
from datahub.core.test.support.views import PermissionModelViewset
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory

factory = APIRequestFactory()


class TestPermissions(APITestMixin):
    """Tests for team permissions"""

    def test_view_returns_200(self):
        """
        Tests view returns 200
        """
        permission = Permission.objects.get(codename='view_permissionmodel')
        permission_group = GroupFactory()
        permission_group.permissions.add(permission)
        team = TeamFactory()
        team.role.groups.add(permission_group)
        user = create_test_user(dit_team=team)
        token = self.get_token(user=user)

        request = factory.get(
            '/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        my_view = PermissionModelViewset.as_view(
            actions={'get': 'list'},
        )
        response = my_view(request)

        assert response.status_code == status.HTTP_200_OK

    def test_view_returns_403(self):
        """
        Tests view returns 403
        """
        user = create_test_user(dit_team=TeamFactory())
        token = self.get_token(user=user)

        request = factory.get(
            '/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        my_view = PermissionModelViewset.as_view(
            actions={'get': 'list'},
        )
        response = my_view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_without_team_returns_403(self):
        """
        Tests view returns 403 for user without team and permission
        """
        user = create_test_user()

        token = self.get_token(user=user)

        request = factory.get(
            '/',
            data={},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        my_view = PermissionModelViewset.as_view(
            actions={'get': 'list'},
        )
        response = my_view(request)

        assert response.status_code == status.HTTP_403_FORBIDDEN
