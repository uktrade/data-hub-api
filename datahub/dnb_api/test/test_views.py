import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from datahub.core.test_utils import APITestMixin
from datahub.dnb_api.constants import FEATURE_FLAG_DNB_COMPANY_SEARCH
from datahub.feature_flag.test.factories import FeatureFlagFactory


@pytest.fixture()
def dnb_company_search_feature_flag():
    """
    Creates the dnb company search feature flag.
    """
    yield FeatureFlagFactory(code=FEATURE_FLAG_DNB_COMPANY_SEARCH)


class TestDNBCompanySearchAPI(APITestMixin):
    """
    DNB Company Search view test case.
    """

    @pytest.mark.parametrize(
        'request_data,response_status_code,response_content',
        (
            pytest.param(
                b'{"arg": "value"}',
                200,
                b'{"took":27}',
                id='successful call to proxied API',
            ),
            pytest.param(
                b'{"arg": "value"}',
                400,
                b'{"error":"msg"}',
                id='proxied API returns a bad request',
            ),
            pytest.param(
                b'{"arg": "value"}',
                500,
                b'{"error":"msg"}',
                id='proxied API returns a server error',
            ),
        ),
    )
    def test_post(
        self,
        dnb_company_search_feature_flag,
        requests_mock,
        request_data,
        response_status_code,
        response_content,
    ):
        """
        Test for POST proxy.
        """
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

    def test_post_no_feature_flag(self, requests_mock):
        """
        Test that POST fails with a 404 when the feature flag is unset.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
        )

        url = reverse('api-v4:dnb-api:company-search')
        response = self.api_client.post(
            url,
            data={'foo': 'bar'},
            content_type='application/json',
        )

        assert response.status_code == 404
        assert requests_mock.called is False

    @override_settings(DNB_SERVICE_BASE_URL=None)
    def test_post_no_dnb_setting(self, dnb_company_search_feature_flag):
        """
        Test that we get an ImproperlyConfigured exception when the DNB_SERVICE_BASE_URL setting
        is not set.
        """
        url = reverse('api-v4:dnb-api:company-search')
        with pytest.raises(ImproperlyConfigured):
            self.api_client.post(
                url,
                data={'foo': 'bar'},
                content_type='application/json',
            )

    @pytest.mark.parametrize(
        'content_type,expected_status_code',
        (
            (None, status.HTTP_406_NOT_ACCEPTABLE),
            ('text/html', status.HTTP_406_NOT_ACCEPTABLE),
            ('application/json', status.HTTP_200_OK),
        ),
    )
    def test_content_type(
        self,
        dnb_company_search_feature_flag,
        requests_mock,
        content_type,
        expected_status_code,
    ):
        """
        Test that 406 is returned if Content Type is not application/json.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
            status_code=status.HTTP_200_OK,
        )

        url = reverse('api-v4:dnb-api:company-search')
        response = self.api_client.post(url, content_type=content_type)

        assert response.status_code == expected_status_code

    def test_unauthenticated_not_authorised(self, requests_mock, dnb_company_search_feature_flag):
        """
        Ensure that a non-authenticated request gets a 401.
        """
        requests_mock.post(
            settings.DNB_SERVICE_BASE_URL + 'companies/search/',
        )

        unauthorised_api_client = self.create_api_client()
        unauthorised_api_client.credentials(Authorization='foo')

        url = reverse('api-v4:dnb-api:company-search')
        response = unauthorised_api_client.post(
            url,
            data={'foo': 'bar'},
            content_type='application/json',
        )

        assert response.status_code == 401
        assert requests_mock.called is False
