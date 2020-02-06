from collections import Counter
from typing import NamedTuple

import pytest
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import APITestMixin, create_test_user
from datahub.metadata.test.factories import TeamFactory


class AdviserPermissionConfig(NamedTuple):
    """Adviser permission configuration for test_filter_by_permission parametrisations."""

    is_superuser: bool = False
    user_permission: str = None
    group_permission: str = None
    team_role_permission: str = None


@pytest.fixture
def advisers():
    """Fixture that creates a fixed set of advisers."""
    factory_kwarg_list = (
        {
            'first_name': 'John',
            'last_name': 'Gravy',
            'dit_team__name': 'Johannesburg',
        },
        {
            'first_name': 'Elisabeth',
            'last_name': 'Gravy',
            'dit_team__name': 'Johannesburg',
        },
        {
            'first_name': 'Anna',
            'last_name': 'George',
            'dit_team__name': 'London',
        },
        {
            'first_name': 'Neil',
            'last_name': 'Coldman',
            'dit_team__name': 'London',
        },
        {
            'first_name': 'Trent',
            'last_name': 'Nort',
            'dit_team__name': 'London',
        },
        {
            'first_name': 'Roger',
            'last_name': 'Grates',
            'dit_team__name': 'London',
        },
        {
            'first_name': 'Roger',
            'last_name': 'Grates',
            'dit_team__name': 'Lisbon',
        },
        {
            'first_name': 'Jennifer',
            'last_name': 'Cakeman',
            'dit_team__name': 'New York',
        },
        {
            'first_name': 'Nigel',
            'last_name': 'Newman',
            'dit_team__name': 'New York',
        },
        {
            # with accent
            'first_name': 'Éla',
            'last_name': 'Pien',
            'dit_team__name': 'Iceland',
        },
        {
            # with middle name
            'first_name': 'Amy Sarah',
            'last_name': 'Dacre',
            'dit_team__name': 'New York',
        },
        {
            'first_name': 'Jessica',
            # with hyphen
            'last_name': 'Samson-James',
            'dit_team__name': 'New York',
        },
        {
            'first_name': 'Jo',
            # with straight apostrophe
            'last_name': "O'Conner",
            'dit_team__name': 'New York',
        },
        {
            'first_name': 'Mary',
            # with curly apostrophe
            'last_name': 'O’Conner',
            'dit_team__name': 'New York',
        },
    )

    yield [AdviserFactory(**kwargs) for kwargs in factory_kwarg_list]


class TestAdviser(APITestMixin):
    """Adviser test case."""

    def test_adviser_list_no_permissions(self):
        """Should return 403"""
        user = create_test_user(dit_team=TeamFactory())
        api_client = self.create_api_client(user=user)
        url = reverse('api-v1:advisor-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_adviser_list_view(self):
        """Should return id and name."""
        AdviserFactory()
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_adviser_list_view_default_sort_order(self):
        """Test default sorting."""
        AdviserFactory(first_name='a', last_name='sorted adviser')
        AdviserFactory(first_name='z', last_name='sorted adviser')
        AdviserFactory(first_name='f', last_name='sorted adviser')

        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result['results']) == 4
        results = result['results']
        assert [res['name'] for res in results] == [
            'a sorted adviser',
            'f sorted adviser',
            # This is the test user making the request
            'Testo Useri',
            'z sorted adviser',
        ]

    @pytest.mark.parametrize('filter_value', (False, True))
    def test_can_filter_by_is_active(self, filter_value):
        """Test filtering by is_active."""
        AdviserFactory.create_batch(5, is_active=not filter_value)
        matching_advisers = AdviserFactory.create_batch(4, is_active=filter_value)
        if filter_value:
            matching_advisers.append(self.user)

        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(
            url,
            data={
                'is_active': filter_value,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data['count'] == len(matching_advisers)
        actual_ids = Counter(str(adviser.pk) for adviser in matching_advisers)
        expected_ids = Counter(result['id'] for result in response_data['results'])
        assert actual_ids == expected_ids

    @pytest.mark.parametrize(
        'terms,expected_results',
        (
            (
                # passing an empty string is the same as omitting the parameter
                # (returns all advisers)
                '',
                [
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Anna', 'George', 'London'),
                    ('Éla', 'Pien', 'Iceland'),
                    ('Elisabeth', 'Gravy', 'Johannesburg'),
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('John', 'Gravy', 'Johannesburg'),
                    ('Mary', 'O’Conner', 'New York'),
                    ('Neil', 'Coldman', 'London'),
                    ('Nigel', 'Newman', 'New York'),
                    ('Roger', 'Grates', 'Lisbon'),
                    ('Roger', 'Grates', 'London'),
                    # default test user
                    ('Testo', 'Useri', 'Aberdeen City Council'),
                    ('Trent', 'Nort', 'London'),
                ],
            ),
            (
                # nothing odd should happen with special characters
                r"%_`~:'()[]{}?*+-|^$\\.&~# \t\n\r\v\f",  # noqa: P103
                [],
            ),
            (
                # non-ASCII characters should not fail
                r'ẽõḉẹã',
                [],
            ),
            (
                'acre',
                [],
            ),
            (
                'Conner',
                [
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                'conner new york',
                [
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                # with extra spaces
                'conner   new  york',
                [
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                # with typo
                'connner new york',
                [],
            ),
            (
                'conner new york london',
                [],
            ),
            (
                'É',
                [
                    ('Éla', 'Pien', 'Iceland'),
                ],
            ),
            (
                'Éla',
                [
                    ('Éla', 'Pien', 'Iceland'),
                ],
            ),
            (
                'Gr',
                [
                    ('Roger', 'Grates', 'Lisbon'),
                    ('Roger', 'Grates', 'London'),
                    ('Elisabeth', 'Gravy', 'Johannesburg'),
                    ('John', 'Gravy', 'Johannesburg'),
                ],
            ),
            (
                'J',
                [
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('John', 'Gravy', 'Johannesburg'),
                    ('Elisabeth', 'Gravy', 'Johannesburg'),
                ],
            ),
            (
                'Ja',
                [
                    ('Jessica', 'Samson-James', 'New York'),
                ],
            ),
            (
                'Jo',
                [
                    ('Jo', "O'Conner", 'New York'),
                    ('John', 'Gravy', 'Johannesburg'),
                    ('Elisabeth', 'Gravy', 'Johannesburg'),
                ],
            ),
            (
                'Joh',
                [
                    ('John', 'Gravy', 'Johannesburg'),
                    ('Elisabeth', 'Gravy', 'Johannesburg'),
                ],
            ),
            (
                'l',
                [
                    ('Roger', 'Grates', 'Lisbon'),
                    ('Anna', 'George', 'London'),
                    ('Neil', 'Coldman', 'London'),
                    ('Roger', 'Grates', 'London'),
                    ('Trent', 'Nort', 'London'),
                ],
            ),
            (
                'N',
                [
                    ('Neil', 'Coldman', 'London'),
                    ('Nigel', 'Newman', 'New York'),
                    ('Trent', 'Nort', 'London'),
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                'Ne',
                [
                    ('Neil', 'Coldman', 'London'),
                    ('Nigel', 'Newman', 'New York'),
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                'New',
                [
                    ('Nigel', 'Newman', 'New York'),
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                'ne lo',
                [
                    ('Neil', 'Coldman', 'London'),
                ],
            ),
            (
                'Ne Yo',
                [
                    ('Nigel', 'Newman', 'New York'),
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                ],
            ),
            (
                'Ni',
                [
                    ('Nigel', 'Newman', 'New York'),
                ],
            ),
            (
                "O'Conner",
                [
                    ('Jo', "O'Conner", 'New York'),
                ],
            ),
            (
                'Sa',
                [
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                ],
            ),
            (
                'York',
                [
                    ('Amy Sarah', 'Dacre', 'New York'),
                    ('Jennifer', 'Cakeman', 'New York'),
                    ('Jessica', 'Samson-James', 'New York'),
                    ('Jo', "O'Conner", 'New York'),
                    ('Mary', 'O’Conner', 'New York'),
                    ('Nigel', 'Newman', 'New York'),
                ],
            ),
            (
                'zzz',
                [],
            ),
        ),
    )
    def test_adviser_autocomplete(self, terms, expected_results, advisers):
        """Tests the adviser autocomplete feature."""
        url = reverse('api-v1:advisor-list')
        response = self.api_client.get(
            url,
            data={
                'autocomplete': terms,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        actual_results = [
            (result['first_name'], result['last_name'], result['dit_team']['name'])
            for result in response_data['results']
        ]
        assert actual_results == expected_results

        assert response_data['count'] == len(expected_results)

    @pytest.mark.parametrize(
        'permission_config,filter_by_permission,should_match',
        (
            (
                AdviserPermissionConfig(user_permission='support.add_permissionmodel'),
                'support.add_permissionmodel',
                True,
            ),
            (
                AdviserPermissionConfig(group_permission='support.add_permissionmodel'),
                'support.add_permissionmodel',
                True,
            ),
            (
                AdviserPermissionConfig(team_role_permission='support.add_permissionmodel'),
                'support.add_permissionmodel',
                True,
            ),
            (
                AdviserPermissionConfig(user_permission='support.add_permissionmodel'),
                'support.view_permissionmodel',
                False,
            ),
            (
                AdviserPermissionConfig(is_superuser=True),
                'support.add_permissionmodel',
                True,
            ),
            (
                AdviserPermissionConfig(),
                'support.add_permissionmodel',
                False,
            ),
            # If the same permission is specified in multiple locations, we should not get
            # duplicate results
            (
                AdviserPermissionConfig(
                    user_permission='support.add_permissionmodel',
                    group_permission='support.add_permissionmodel',
                    team_role_permission='support.add_permissionmodel',
                ),
                'support.add_permissionmodel',
                True,
            ),
            # If the permission does not exist, even a super user shouldn't be returned
            (
                AdviserPermissionConfig(is_superuser=True),
                'non-existent.permission',
                False,
            ),
        ),
    )
    def test_filter_by_permission(
        self,
        permission_config,
        filter_by_permission,
        should_match,
    ):
        """Test the `has_permission` filter in various cases."""
        user = create_test_user(
            permission_codenames=('view_advisor',),
            is_superuser=permission_config.is_superuser,
            dit_team=TeamFactory(),
        )

        if permission_config.user_permission:
            permission = _get_permission(permission_config.user_permission)
            user.user_permissions.add(permission)

        if permission_config.group_permission:
            group = _make_group('group 1', permission_config.group_permission)
            user.groups.add(group)

        if permission_config.team_role_permission:
            group = _make_group('group 2', permission_config.team_role_permission)
            user.dit_team.role.groups.add(group)

        api_client = self.create_api_client(user=user)

        url = reverse('api-v1:advisor-list')
        response = api_client.get(
            url,
            data={
                'permissions__has': filter_by_permission,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        if should_match:
            assert response_data['count'] == 1
            result = response_data['results'][0]
            assert result['id'] == str(user.pk)
        else:
            assert response_data['count'] == 0


def _get_permission(name):
    app_label, _, codename = name.partition('.')
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def _make_group(group_name, permission_name):
    permission = _get_permission(permission_name)

    group = Group.objects.create(name=group_name)
    group.permissions.add(permission)

    return group
