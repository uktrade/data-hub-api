import pytest
from django.conf import settings
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
        # api_client.get transforms data into querystring hence generic is used here
        response = self.api_client.generic(
            'POST',
            url,
            data=request_data,
            content_type='application/json',
        )

        assert response.status_code == response_status_code
        assert response.content == response_content
        assert requests_mock.last_request.body == request_data
