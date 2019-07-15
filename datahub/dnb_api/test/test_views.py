import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin


class TestDNBCompanySearchAPI(APITestMixin):
    """
    DNB Company Search view test case.
    """

    @pytest.mark.parametrize(
        'request_data,response_status_code,response_content',
        (
            (
                b'{"arg": "value"}',
                200,
                b'{"took":27}',
            ),
            (
                b'{"arg": "value"}',
                400,
                b'{"error":"msg"}',
            ),
            (
                b'{"arg": "value"}',
                500,
                b'{"error":"msg"}',
            ),
        ),
    )
    def test_post(self, requests_mock, request_data, response_status_code, response_content):
        """Test for GET proxy."""
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
            status_code=response_status_code,
            content=response_content,
        )

        url = reverse('api-v4:dnb-api:company-search')
        response = self.api_client.post(
            url,
            data=request_data,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert response.content == response_content
        assert requests_mock.last_request.body == request_data

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
            ('application/json', status.HTTP_200_OK),
        ),
    )
    def test_content_type(self, requests_mock, content_type, expected_status_code):
        """Test that 406 is returned if Content Type is not application/json."""
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
            status_code=status.HTTP_200_OK,
        )

        url = reverse('api-v4:dnb-api:company-search')
        response = self.api_client.post(url, content_type=content_type)

        assert response.status_code == expected_status_code
