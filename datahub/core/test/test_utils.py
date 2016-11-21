from unittest import mock

from datahub.core.test_utils import LeelooTestCase
from datahub.core.utils import CDMSUserBackend


class TestCDMSUserBackend(LeelooTestCase):
    """Test case for CDMS Custom user Backend."""

    @mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
    def test_invalid_credentials(self, korben_auth_mock):
        """Test empty result with invalid credentials."""
        korben_auth_mock.return_value = False
        backend = CDMSUserBackend()

        self.assertIsNone(backend.authenticate(username='invalid', password='invalid'))
        self.assertFalse(korben_auth_mock.called)

    @mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
    def test_invalid_credentials_with_valid_user(self, korben_auth_mock):
        """Test empty result with invalid password for valid user."""
        user = self.get_user()
        korben_auth_mock.return_value = False
        backend = CDMSUserBackend()

        self.assertIsNone(backend.authenticate(username=user.username, password='invalid'))
        korben_auth_mock.assert_called_with(username=user.username, password='invalid')

    @mock.patch('datahub.core.utils.CDMSUserBackend.korben_authenticate')
    def test_valid_user(self, korben_auth_mock):
        """Test valid result with valid creds and user."""
        user = self.get_user()
        korben_auth_mock.return_value = True
        backend = CDMSUserBackend()

        result = backend.authenticate(username=user.username, password='assume_valid')
        korben_auth_mock.assert_called_with(username=user.username, password='assume_valid')

        self.assertEqual(result.pk, user.pk)
