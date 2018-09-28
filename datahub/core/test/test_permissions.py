from unittest.mock import Mock

import pytest

from datahub.core.permissions import HasPermissions


class TestHasPermissions:
    """Tests the HasPermissions permissions class."""

    @pytest.mark.parametrize(
        'required_permissions,user_permissions,expected_result',
        (
            ({'perm1', 'perm2'}, {'perm1', 'perm2', 'perm3'}, True),
            ({'perm1', 'perm2'}, {'perm1', 'perm2'}, True),
            ({'perm1', 'perm2'}, {'perm2', 'perm3'}, False),
            ({'perm1', 'perm2'}, {'perm2'}, False),
            ({'perm1', 'perm2'}, (), False),
        ),
    )
    def test_has_permissions(self, required_permissions, user_permissions, expected_result):
        """Tests has_permission() for various cases."""
        user = Mock(has_perm=lambda perm: perm in user_permissions)
        request = Mock(user=user)
        view = Mock()
        has_permissions = HasPermissions(*required_permissions)
        assert has_permissions.has_permission(request, view) == expected_result

    def test_raises_error_if_no_permissions_provided(self):
        """Tests that an error is raised if no permissions are provided."""
        with pytest.raises(ValueError):
            HasPermissions()
