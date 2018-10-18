from unittest.mock import Mock

import pytest
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse

from datahub.core.admin import (
    custom_add_permission,
    custom_change_permission,
    custom_delete_permission,
    get_change_link,
    get_change_url,
    RawIdWidget,
)
from datahub.core.test.support.factories import BookFactory
from datahub.core.test.support.models import Book


class TestRawIdWidget:
    """Tests for RawIdWidget."""

    def test_get_context_without_value(self):
        """Tests get_context() when no value is supplied."""
        widget = RawIdWidget(Book)
        assert widget.get_context('test-widget', None, {}) == {
            'link_title': 'Look up book',
            'related_url': '/admin/support/book/?_to_field=id',
            'widget': {
                'attrs': {
                    'class': 'vForeignKeyRawIdAdminField',
                },
                'is_hidden': False,
                'name': 'test-widget',
                'required': False,
                'template_name': 'admin/widgets/foreign_key_raw_id.html',
                'type': 'text',
                'value': None,
            },
        }

    @pytest.mark.django_db
    def test_get_context_with_valid_value(self):
        """Tests get_context() when a valid value is supplied."""
        book = BookFactory()
        widget = RawIdWidget(Book)

        change_route_name = admin_urlname(Book._meta, 'change')
        change_url = reverse(change_route_name, args=(book.pk,))

        changelist_route_name = admin_urlname(Book._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        assert widget.get_context('test-widget', str(book.pk), {}) == {
            'link_label': str(book),
            'link_title': 'Look up book',
            'link_url': change_url,
            'related_url': f'{changelist_url}?_to_field=id',
            'widget': {
                'attrs': {
                    'class': 'vForeignKeyRawIdAdminField',
                },
                'is_hidden': False,
                'name': 'test-widget',
                'required': False,
                'template_name': 'admin/widgets/foreign_key_raw_id.html',
                'type': 'text',
                'value': str(book.pk),
            },
        }

    @pytest.mark.parametrize(
        'value',
        ('123', 'b77ffa2a-bce8-440b-9d8a-b4f247f194dd'),
    )
    @pytest.mark.django_db
    def test_get_context_with_invalid_value(self, value):
        """Tests get_context() when an invalid value is supplied."""
        widget = RawIdWidget(Book)

        changelist_route_name = admin_urlname(Book._meta, 'changelist')
        changelist_url = reverse(changelist_route_name)

        assert widget.get_context('test-widget', value, {}) == {
            'link_label': '',
            'link_title': 'Look up book',
            'link_url': '',
            'related_url': f'{changelist_url}?_to_field=id',
            'widget': {
                'attrs': {
                    'class': 'vForeignKeyRawIdAdminField',
                },
                'is_hidden': False,
                'name': 'test-widget',
                'required': False,
                'template_name': 'admin/widgets/foreign_key_raw_id.html',
                'type': 'text',
                'value': value,
            },
        }


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


class TestGetChangeURL:
    """Tests for get_change_url()."""

    @pytest.mark.django_db
    def test_generates_urls_for_saved_objects(self):
        """Test that a valid change URL is generated."""
        book = BookFactory()
        assert get_change_url(book) == (
            f'/admin/support/book/{book.pk}/change/'
        )

    def test_returns_empty_string_if_no_pk(self):
        """Test that if the object has no pk, an empty URL is returned."""
        book = BookFactory.build()
        assert get_change_url(book) == ''

    def test_returns_empty_string_if_obj_is_none(self):
        """Test that if None is passed, an empty URL is returned."""
        assert get_change_url(None) == ''


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
