from cgi import parse_header

import pytest
from django.test import Client
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from datahub.core.test.support.factories import MetadataModelFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user


class TestReportAdmin(AdminTestMixin):
    """Tests for the report list page."""

    @pytest.mark.parametrize(
        'url',
        (
            reverse('admin-report:index'),
            reverse('admin-report:download-report', kwargs={'report_id': 'test-report'}),
        ),
    )
    def test_redirects_to_login_page_if_not_logged_in(self, url):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        client = Client()

        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize(
        'url',
        (
            reverse('admin-report:index'),
            reverse('admin-report:download-report', kwargs={'report_id': 'test-report'}),
        ),
    )
    def test_redirects_to_login_page_if_not_staff(self, url):
        """Test that the view redirects to the login page if the user isn't a member of staff."""
        user = create_test_user(is_staff=False, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    def test_200_if_staff(self):
        """Test that the view returns a 200 response if the user is an admin user."""
        url = reverse('admin-report:index')
        user = create_test_user(is_staff=True, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_non_existent_report_download(self):
        """
        Test that the view returns a 404 response if the report ID does not refer to a
        registered report.
        """
        url = reverse('admin-report:download-report', kwargs={'report_id': 'non-existent-report'})
        user = create_test_user(is_staff=True, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_report_download_without_permission(self):
        """
        Test that the view returns a 403 response if the staff user does not have the
        correct permissions.
        """
        url = reverse('admin-report:download-report', kwargs={'report_id': 'test-report'})
        user = create_test_user(permission_codenames=(), is_staff=True, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @freeze_time('2018-01-01 11:12:13')
    def test_report_download(self):
        """Test the download of a report."""
        obj = MetadataModelFactory()
        url = reverse('admin-report:download-report', kwargs={'report_id': 'test-report'})

        user = create_test_user(
            permission_codenames=('change_metadatamodel',),
            is_staff=True,
            password=self.PASSWORD,
        )

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert parse_header(response.get('Content-Type')) == ('text/csv', {'charset': 'utf-8'})
        assert parse_header(response.get('Content-Disposition')) == (
            'attachment', {'filename': 'Test report - 2018-01-01-11-12-13.csv'},
        )
        assert response.getvalue().decode('utf-8-sig') == f"""Test ID,Name\r
{str(obj.pk)},{obj.name}\r
"""
