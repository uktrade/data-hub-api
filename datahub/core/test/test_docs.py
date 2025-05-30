import pytest
from django.urls import reverse
from rest_framework import status

from datahub.core.test_utils import AdminTestMixin, create_test_user, get_admin_user


class TestDocsSwaggerUIView(AdminTestMixin):
    """Test the Swagger UI view."""

    @pytest.mark.parametrize('version', ['v1', 'v3', 'v4'])
    def test_redirects_to_login_page_if_not_logged_in(self, client, version):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        url = reverse(f'api-{version}:swagger-ui-{version}')
        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)

    @pytest.mark.parametrize('version', ['v1', 'v3', 'v4'])
    def test_returns_200_if_authenticated(self, client, version):
        """Test that a 200 is returned if the user is authenticated via the admin site."""
        url = reverse(f'api-{version}:swagger-ui-{version}')
        user = create_test_user(is_staff=True, password=self.PASSWORD)

        client = self.create_client(user=user)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK


class TestDocsSchemaView(AdminTestMixin):
    """Test the OpenAPI schema view."""

    @pytest.mark.parametrize('version', ['v1', 'v3', 'v4'])
    def test_returns_200_if_logged_in(self, client, version):
        """Test that a 200 is returned if a user is logged in using session authentication.

        This is primarily to make sure that the page is functioning and no views are breaking it.
        """
        password = 'test-password'
        user = get_admin_user(password=password)
        client.login(username=user.email, password=password)

        url = reverse(f'api-{version}:openapi-schema-{version}')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize('version', ['v1', 'v3', 'v4'])
    def test_returns_content_if_logged_in(self, client, version):
        """Tests that some content is loaded if the user is logged in."""
        password = 'test-password'
        user = get_admin_user(password=password)
        client.login(username=user.email, password=password)

        url = reverse(f'api-{version}:openapi-schema-{version}')
        response = client.get(url)

        assert len(response.content) > 0
        lower_case_content = response.content.lower()
        assert b'openapi' in lower_case_content
        assert b'info' in lower_case_content
        assert b'paths' in lower_case_content

    @pytest.mark.parametrize('version', ['v1', 'v3', 'v4'])
    def test_redirects_to_login_page_if_not_logged_in(self, client, version):
        """Test that the view redirects to the login page if the user isn't authenticated."""
        url = reverse(f'api-{version}:openapi-schema-{version}')
        response = client.get(url)

        assert response.status_code == status.HTTP_302_FOUND
        assert response['Location'] == self.login_url_with_redirect(url)
