import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from oauth2_provider.models import Application
from rest_framework.test import APIClient


def get_test_user():
    """Return the test user."""

    test, _ = User.objects.get_or_create(username='Test')
    test.set_password('password')
    return test


class LeelooTest:
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    def __init__(self):
        self.user = get_test_user()
        self.application = self.get_application()
        self.token = self.get_token()

    def get_logged_in_api_client(self):
        """
        Login using the OAuth2 authentication.

        1) Create an application instance, if necessary
        2) Generate the token
        3) Add the auth credentials to the header
        """
        client = APIClient()
        client.credentials(HTTP_AUHTORIZATION='Authorization: Bearer {token}'.format(token=self.token))
        return client

    def get_token(self):
        """Get access token for user test."""

        client = RequestsClient()
        client.login(username=self.application.client_id, password=self.application.client_secret)
        url = reverse('token')
        data = {
            'grant_type': 'password',
            'username': self.user.username,
            'password': 'password'
        }
        import ipdb; ipdb.set_trace()
        response = client.post(url, data=data)

    def get_application(self):
        """Return the test application."""

        application, _ = Application.objects.get_or_create(
                user=get_test_user(),
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_PASSWORD,
                name='Test client'
            )
        return application
