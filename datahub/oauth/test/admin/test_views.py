import re
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.test import Client, override_settings
from django.urls import reverse
from django.utils.timezone import now
from freezegun import freeze_time
from rest_framework import status

from datahub.company.test.factories import AdviserFactory
from datahub.core.test_utils import AdminTestMixin, create_test_user
from datahub.oauth.admin.forms import AddAccessTokenForm, NO_SSO_EMAIL_USER_ID_MESSAGE

admin_index_url = reverse('admin:index')
add_access_token_url = reverse('admin-oauth:add-access-token')


@pytest.mark.usefixtures('local_memory_cache')
class TestAddAccessTokenAdminView(AdminTestMixin):
    """Tests for the add access token admin view."""

    @pytest.mark.parametrize('http_method', ('get', 'post'))
    def test_redirects_to_login_page_if_not_logged_in(self, http_method):
        """The view should redirect to the login page if the user isn't authenticated."""
        client = Client()
        response = client.generic(http_method, add_access_token_url)
        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(add_access_token_url)

    @pytest.mark.parametrize('http_method', ('get', 'post'))
    def test_redirects_to_login_page_if_not_staff(self, http_method):
        """The view should redirect to the login page if the user isn't a member of staff."""
        user = create_test_user(is_staff=False, password=self.PASSWORD)
        client = self.create_client(user=user)

        response = client.generic(http_method, add_access_token_url)
        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(add_access_token_url)

    @pytest.mark.parametrize('http_method', ('get', 'post'))
    def test_permission_denied_if_staff_and_not_superuser(self, http_method):
        """
        The view should return a 403 response if the staff user does not have the add adviser
        permission.
        """
        user = create_test_user(is_staff=True, password=self.PASSWORD)
        client = self.create_client(user=user)

        response = client.generic(http_method, add_access_token_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(ENABLE_ADMIN_ADD_ACCESS_TOKEN_VIEW=False)
    def test_returns_404_when_view_disable(self):
        """A 404 should be is returned if the view is disabled via a setting."""
        user = create_test_user(is_staff=True, is_superuser=True, password=self.PASSWORD)
        client = self.create_client(user=user)

        response = client.get(add_access_token_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_displays_form_if_authorised(self):
        """The form should be displayed for an authorised user."""
        user = create_test_user(is_staff=True, is_superuser=True, password=self.PASSWORD)
        client = self.create_client(user=user)

        response = client.get(add_access_token_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'Expires in' in response.rendered_content
        assert response.template_name.endswith('/add_access_token.html')
        assert isinstance(response.context['form'], AddAccessTokenForm)

    def test_returns_error_if_adviser_has_no_sso_email_user_id(self):
        """If an adviser without an SSO email user ID is specified, an error should be returned."""
        user = create_test_user(is_staff=True, is_superuser=True, password=self.PASSWORD)
        adviser = AdviserFactory(sso_email_user_id=None)
        client = self.create_client(user=user)

        data = {
            'adviser': adviser.pk,
            'expires_in_hours': 10,
        }
        response = client.post(add_access_token_url, data=data)
        assert response.status_code == status.HTTP_200_OK

        form = response.context['form']
        assert form.errors == {
            'adviser': [NO_SSO_EMAIL_USER_ID_MESSAGE],
        }

    @pytest.mark.parametrize('expires_in_hours', (1, 10))
    def test_adds_access_token_on_success(self, expires_in_hours):
        """The generated access token should be stored in the cache."""
        user = create_test_user(is_staff=True, is_superuser=True, password=self.PASSWORD)
        sso_email_user_id = 'id@datahub.test'
        adviser = AdviserFactory(sso_email_user_id=sso_email_user_id)
        client = self.create_client(user=user)

        frozen_time = now()
        with freeze_time(frozen_time):
            data = {
                'adviser': adviser.pk,
                'expires_in_hours': expires_in_hours,
            }
            response = client.post(add_access_token_url, data=data, follow=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.redirect_chain == [
            (admin_index_url, status.HTTP_302_FOUND),
        ]
        messages = list(response.context['messages'])
        assert len(messages) == 1

        success_message_text = messages[0].message
        search_pattern = r'<code style="user-select: all">(?P<token>[0-9a-zA-Z_-]+)</code>'
        match = re.search(search_pattern, success_message_text)
        assert match

        token = match.group('token')
        expected_expiry_time = frozen_time + timedelta(hours=expires_in_hours)

        with freeze_time(expected_expiry_time - timedelta(seconds=1)):
            assert cache.get(f'access_token:{token}') == {
                'email': adviser.email,
                'sso_email_user_id': sso_email_user_id,
            }

        with freeze_time(expected_expiry_time):
            assert cache.get(f'access_token:{token}') is None
