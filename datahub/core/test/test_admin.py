from unittest.mock import Mock

import pytest

from datahub.core.admin import (
    custom_add_permission,
    custom_change_permission,
    custom_delete_permission,
    get_change_link,
)
from datahub.core.test.support.factories import BookFactory


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


class TestGetChangeLink:
    """Tests for get_change_link()."""

    @pytest.mark.django_db
    def test_generates_links_for_saved_objects(self):
        """Test that a valid change link is generated."""
        book = BookFactory()
        assert get_change_link(book) == (
            f'<a href="/admin/support/book/{book.pk}/change/">{book.name}</a>'
        )

    def test_returns_empty_string_if_no_pk(self):
        """Test that if the object has no pk, an empty link is returned."""
        book = BookFactory.build()
        assert get_change_link(book) == ''

    def test_returns_empty_string_if_obj_is_none(self):
        """Test that if None is passed, an empty link is returned."""
        assert get_change_link(None) == ''
