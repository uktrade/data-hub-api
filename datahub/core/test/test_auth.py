import pytest
from django.urls import reverse
from rest_framework import status


def _url():
    return 'http://testserver' + reverse('test-paas-ip')


@pytest.mark.django_db
@pytest.mark.urls('datahub.core.test.support.urls')
class TestPaaSIPAuthentication:
    """Tests PaaS IP authentication when using PaaSIPAuthentication."""

    @pytest.mark.parametrize(
        'get_kwargs,expected_json',
        (
            (
                # If no X-Forwarded-For header
                {},
                {'detail': 'Incorrect authentication credentials.'},
            ),
            (
                # If second-to-last X-Forwarded-For header isn't whitelisted
                {
                    'HTTP_X_FORWARDED_FOR': '9.9.9.9, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
            (
                # If the only IP address in X-Forwarded-For is whitelisted
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
            (
                # If the only IP address in X-Forwarded-For isn't whitelisted
                {
                    'HTTP_X_FORWARDED_FOR': '123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
            (
                # If third-to-last IP in X-Forwarded-For header is whitelisted
                {
                    'HTTP_X_FORWARDED_FOR': '1.2.3.4, 124.124.124, 123.123.123.123',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
            (
                # If last of 3 IPs in X-Forwarded-For header is whitelisted
                {
                    'HTTP_X_FORWARDED_FOR': '124.124.124, 123.123.123.123, 1.2.3.4',
                },
                {'detail': 'Incorrect authentication credentials.'},
            ),
        ),
    )
    def test_401_returned_when_invalid_ip(self, api_client, get_kwargs, expected_json):
        """
        If the client IP is not authorised to access, then a 401 is returned.
        """
        resolved_get_kwargs = get_kwargs
        response = api_client.get(
            _url(),
            **resolved_get_kwargs,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == expected_json

    def test_empty_object_returned_with_authentication_3_ips(self, api_client):
        """
        If the X-Forwarded-For header is correct, with an extra IP address prepended
        to the X-Forwarded-For then the correct data is returned.
        """
        response = api_client.get(
            _url(),
            HTTP_X_FORWARDED_FOR='3.3.3.3, 1.2.3.4, 123.123.123.123',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'content': 'paas-ip-test-view'}

    def test_empty_object_returned_with_authentication(self, api_client):
        """If the Authorization and X-Forwarded-For headers are correct, then
        the correct data is returned
        """
        response = api_client.get(
            _url(),
            HTTP_X_FORWARDED_FOR='1.2.3.4, 123.123.123.123',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'content': 'paas-ip-test-view'}

    def test_paas_ip_check_disabled(self, api_client, settings, caplog):
        """If PaaS IP check is disabled and X-Forwarded-For headers are incorrect, then
        the correct data is returned
        """
        caplog.set_level('WARNING')

        settings.DISABLE_PAAS_IP_CHECK = True
        response = api_client.get(
            _url(),
            HTTP_X_FORWARDED_FOR='1.2.3.5',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'content': 'paas-ip-test-view'}
        assert 'PaaS IP check authentication is disabled.' in caplog.text
