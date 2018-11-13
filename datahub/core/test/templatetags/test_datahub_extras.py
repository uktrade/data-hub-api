from unittest.mock import Mock
from uuid import uuid4

import pytest

from datahub.core.templatetags.datahub_extras import (
    admin_change_link,
    admin_change_url,
    verbose_name_for_count,
)
from datahub.core.test.support.factories import BookFactory


def test_admin_change_url():
    """Test that admin_change_url() returns the URL to the change page for an object."""
    book = BookFactory.build(pk=uuid4())
    assert admin_change_url(book) == f'/admin/support/book/{book.pk}/change/'


class TestAdminChangeLink:
    """Tests admin_change_link()."""

    def test_admin_change_link(self):
        """Test that admin_change_url() returns an anchor tag to the change page for an object."""
        book = BookFactory.build(pk=uuid4())
        assert admin_change_link(book) == (
            f'<a href="/admin/support/book/{book.pk}/change/">{book}</a>'
        )

    def test_admin_change_link_target_blank(self):
        """
        Test that admin_change_url() returns an anchor tag with target="_blank" to the change
        page for an object.
        """
        book = BookFactory.build(pk=uuid4())
        assert admin_change_link(book, True) == (
            f'<a href="/admin/support/book/{book.pk}/change/" target="_blank">{book}</a>'
        )


@pytest.mark.parametrize(
    'count,expected_result',
    (
        (0, 'plural'),
        (1, 'singular'),
        (2, 'plural'),
    ),
)
def test_verbose_name_for_count(count, expected_result):
    """
    Test that verbose_name_for_count() returns the correct verbose name form for various counts.
    """
    mock_model_meta = Mock(
        verbose_name='singular',
        verbose_name_plural='plural',
    )
    assert verbose_name_for_count(count, mock_model_meta) == expected_result
