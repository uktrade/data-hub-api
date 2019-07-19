import pytest
from django.urls import reverse
from rest_framework import status

from datahub.core.test_utils import get_admin_user


@pytest.mark.django_db
class TestDocsSchemaView:
    """Test the OpenAPI schema view."""

    def test_returns_200_if_logged_in(self, client):
        """
        Test that a 200 is returned if a user is logged in using session authentication.

        This is primarily to make sure that the page is functioning and no views are breaking it.
        """
        password = 'test-password'
        user = get_admin_user(password=password)
        client.login(username=user.email, password=password)

        url = reverse('api-docs:openapi-schema')
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_returns_403_if_not_logged_in(self, client):
        """Test that a 403 error is returned if the user is not logged in."""
        url = reverse('api-docs:openapi-schema')
        response = client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
