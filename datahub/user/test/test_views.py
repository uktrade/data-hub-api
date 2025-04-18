import factory
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test.factories import GroupFactory, PermissionFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.feature_flag.test.factories import UserFeatureFlagFactory, UserFeatureFlagGroupFactory
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
            'sso_user_id': str(user_test.sso_user_id),
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
            'active_features': [],
            'active_feature_groups': [],
        }

    def test_who_am_i_active_features(self):
        """Active features should include the user's selected active features."""
        feature_flag = UserFeatureFlagFactory(code='test-feature', is_active=True)
        inactive_feature_flag = UserFeatureFlagFactory(code='inactive-feature', is_active=False)

        active_feature_flag_group = UserFeatureFlagGroupFactory(code='test-group', is_active=True)

        active_group_feature_flag = UserFeatureFlagFactory(
            code='active-group-feature',
            is_active=True,
        )
        inactive_group_feature_flag = UserFeatureFlagFactory(
            code='inactive-group-feature',
            is_active=False,
        )
        active_feature_flag_group.features.add(
            active_group_feature_flag,
            inactive_group_feature_flag,
        )
        inactive_feature_flag_group = UserFeatureFlagGroupFactory(
            code='test-inactive-group',
            is_active=False,
        )
        inactive_feature_flag_group.features.add(
            UserFeatureFlagFactory(
                code='irrelevant',
                is_active=True,
            ),
        )

        UserFeatureFlagFactory(code='another-feature', is_active=True)

        user = create_test_user()
        user.features.add(feature_flag, inactive_feature_flag)
        user.feature_groups.add(active_feature_flag_group, inactive_feature_flag_group)

        api_client = self.create_api_client(user=user)

        url = reverse('who_am_i')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert 'active_features' in response_data
        assert set(response_data['active_features']) == {'test-feature', 'active-group-feature'}

    def test_who_am_i_active_feature_groups(self):
        """Active feature groups should include the user's selected active feature groups."""
        active_feature_flag_group1 = UserFeatureFlagGroupFactory(
            code='test-group1',
            is_active=True,
        )
        active_feature_flag_group2 = UserFeatureFlagGroupFactory(
            code='test-group2',
            is_active=True,
        )
        inactive_feature_flag_group = UserFeatureFlagGroupFactory(
            code='test-inactive-group',
            is_active=False,
        )

        UserFeatureFlagFactory(code='another-feature', is_active=True)

        user = create_test_user()
        user.feature_groups.add(
            active_feature_flag_group1,
            active_feature_flag_group2,
            inactive_feature_flag_group,
        )

        api_client = self.create_api_client(user=user)

        url = reverse('who_am_i')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert 'active_features' in response_data
        assert set(response_data['active_feature_groups']) == {'test-group1', 'test-group2'}
