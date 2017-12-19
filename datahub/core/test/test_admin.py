from unittest.mock import Mock

from datahub.core.admin import (
    custom_add_permission, custom_change_permission, custom_delete_permission
)


def test_add_change_permission():
    """Tests that the decorator correctly overrides has_add_permission()."""
    @custom_add_permission('custom_permission')
    class Admin:
        opts = Mock(app_label='admin')

        def has_add_permission(self, request, obj=None):
            return False

    request = Mock()
    admin = Admin()
    admin.has_add_permission(request)

    request.user.has_perm.assert_called_once_with('admin.custom_permission')


def test_custom_change_permission():
    """Tests that the decorator correctly overrides has_change_permission()."""
    @custom_change_permission('custom_permission')
    class Admin:
        opts = Mock(app_label='admin')

        def has_change_permission(self, request, obj=None):
            return False

    request = Mock()
    admin = Admin()
    admin.has_change_permission(request)

    request.user.has_perm.assert_called_once_with('admin.custom_permission')


def test_custom_delete_permission():
    """Tests that the decorator correctly overrides has_delete_permission()."""
    @custom_delete_permission('custom_permission')
    class Admin:
        opts = Mock(app_label='admin')

        def has_delete_permission(self, request, obj=None):
            return False

    request = Mock()
    admin = Admin()
    admin.has_delete_permission(request)

    request.user.has_perm.assert_called_once_with('admin.custom_permission')
