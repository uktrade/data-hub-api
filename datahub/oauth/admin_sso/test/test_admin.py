from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.urls import reverse

from datahub.core.test_utils import AdminTestMixin

pytestmark = pytest.mark.django_db


class TestAdminSite(AdminTestMixin):
    """Test that admin site login and logout views have been replaced with OAuth2 equivalents."""

    @patch('datahub.oauth.admin_sso.admin.login')
    def test_oauth2_login_view_is_called_when_requesting_admin_login(self, _login):
        """Tests that OAuth2 login view is called when accessing admin login."""
        _login.return_value = HttpResponse()

        login_url = reverse('admin:login')
        self.client.get(login_url)

        _login.assert_called_once()

    @patch('datahub.oauth.admin_sso.admin.logout')
    def test_oauth2_login_view_is_called_when_requesting_admin_logout(self, _logout):
        """Tests that OAuth2 logout view is called when accessing admin logout."""
        _logout.return_value = HttpResponse()

        logout_url = reverse('admin:logout')
        self.client.get(logout_url)

        _logout.assert_called_once()
