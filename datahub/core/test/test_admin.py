from unittest.mock import Mock

from datahub.core.admin import custom_change_permission


def test_custom_change_permission():
    """Tests that the descoration correctly overrides has_change_permission()."""
    @custom_change_permission('custom_permission')
    class Admin:
        opts = Mock(app_label='admin')

        def has_change_permission(self, request, obj=None):
            return False

    request = Mock()
    admin = Admin()
    admin.has_change_permission(request)

    request.user.has_perm.assert_called_once_with('admin.custom_permission')
