import io
from unittest.mock import Mock

import pytest
from django.contrib import messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.urls import reverse
from rest_framework import status

from datahub.core.admin import (
    custom_add_permission,
    custom_change_permission,
    custom_delete_permission,
    custom_view_permission,
    format_json_as_html,
    get_change_link,
    get_change_url,
    RawIdWidget,
)
from datahub.core.test.support.factories import BookFactory
from datahub.core.test.support.models import Book
from datahub.core.test.support.views import MAX_UPLOAD_SIZE


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
                    'class': 'vUUIDField',
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
                    'class': 'vUUIDField',
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
                    'class': 'vUUIDField',
                },
                'is_hidden': False,
                'name': 'test-widget',
                'required': False,
                'template_name': 'admin/widgets/foreign_key_raw_id.html',
                'type': 'text',
                'value': value,
            },
        }


def test_custom_view_permission():
    """Tests that the decorator correctly overrides has_view_permission()."""
    @custom_view_permission('custom_permission')
    class Admin:
        opts = Mock(app_label='admin')

        def has_view_permission(self, request, obj=None):
            return False

    request = Mock()
    admin = Admin()
    admin.has_view_permission(request)

    request.user.has_perm.assert_called_once_with('admin.custom_permission')


class TestMaxUploadSize:
    """Tests the max_upload_size decorator."""

    @pytest.mark.parametrize(
        'file_size,error_expected',
        (
            (MAX_UPLOAD_SIZE, False),
            (MAX_UPLOAD_SIZE + 1, True),
        ),
    )
    @pytest.mark.urls('datahub.core.test.support.urls')
    @pytest.mark.django_db
    def test_rejects_large_files(self, file_size, error_expected, client):
        """
        Test that the max_upload_size() rejects files above the set limit.

        This test uses the datahub.core.test.support.views.max_upload_size_view view.
        """
        file = io.BytesIO(b'-' * file_size)
        file.name = 'test.csv'

        url = reverse('test-max-upload-size')
        response = client.post(
            url,
            data={
                'file': file,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        messages = list(response.context['messages'])

        if error_expected:
            assert len(messages) == 1
            assert messages[0].level == django_messages.ERROR
            assert messages[0].message == (
                'The file test.csv was too large. Files must be less than 50 bytes.'
            )
        else:
            assert not messages


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


class TestFormatJsonAsHtml:
    """Tests for format_json_as_html()."""

    @pytest.mark.parametrize(
        'value,expected_output',
        (
            (
                None,
                '<pre>null</pre>',
            ),
            (
                {1: '<'},
                """<pre>{
  &quot;1&quot;: &quot;&lt;&quot;
}</pre>""",
            ),
        ),
    )
    def test_format_json_as_html(self, value, expected_output):
        """Test that various values are serialised and escaped as expected."""
        assert format_json_as_html(value) == expected_output
