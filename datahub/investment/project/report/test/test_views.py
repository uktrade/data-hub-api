from uuid import uuid4

from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.investment.project.report.models import SPIReportPermission
from datahub.investment.project.report.test.factories import SPIReportFactory


class TestGetSPIReport(AdminTestMixin):
    """Tests for get spi report view."""

    def test_fails_without_permissions(self, api_client):
        """Should redirect to login page."""
        report = SPIReportFactory()
        url = reverse(
            'investment-report:download-spi-report',
            kwargs={
                'pk': report.pk,
            },
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    def test_user_with_permission_can_get_report(self):
        """Test get report by a user with permission."""
        report = SPIReportFactory()

        url = reverse(
            'investment-report:download-spi-report',
            kwargs={
                'pk': report.pk,
            },
        )
        user = create_test_user(
            is_staff=True,
            password=self.PASSWORD,
            permission_codenames=(
                SPIReportPermission.view,
            ),
        )
        client = self.create_client(user=user)
        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert report.s3_key in response.url

    def test_user_without_permission_cannot_get_report(self):
        """Test that user without permission cannot get a report."""
        report = SPIReportFactory()
        url = reverse(
            'investment-report:download-spi-report',
            kwargs={
                'pk': report.pk,
            },
        )
        user = create_test_user(
            is_staff=True,
            password=self.PASSWORD,
            permission_codenames=(),
        )
        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_restricted_user_cannot_get_non_existent_report(self):
        """Test user cannot get a report that doesn't exist."""
        url = reverse(
            'investment-report:download-spi-report',
            kwargs={
                'pk': uuid4(),
            },
        )
        user = create_test_user(
            is_staff=True,
            password=self.PASSWORD,
            permission_codenames=(
                SPIReportPermission.view,
            ),
        )
        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
