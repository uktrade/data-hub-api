import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    Timeout,
)
from rest_framework import status

from datahub.company.export_wins_api import (
    export_wins,
    ExportWinsAPIConnectionError,
    ExportWinsAPIHTTPError,
    ExportWinsAPITimeoutError,
)
from datahub.company.test.factories import CompanyFactory
from datahub.core.test_utils import APITestMixin, HawkMockJSONResponse


class TestExportWinsApi(APITestMixin):
    """
    Tests functionality to obtain export wins for a company
    first by getting match if with a post to the company matching service
    and then getting export wins for from export wins API and error handling.
    """

    @pytest.mark.parametrize(
        'build_company,expected_result',
        (
            (
                lambda: CompanyFactory(
                    id='00000000-0000-0000-0000-000000000000',
                    name='Name 1',
                    company_number='00000000',
                    duns_number='111111',
                    address_postcode='W1',
                    reference_code='22222',
                ),
                {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'company_name': 'Name 1',
                    'companies_house_id': '00000000',
                    'duns_number': '111111',
                    'postcode': 'W1',
                    'cdms_ref': '22222',
                },
            ),
            (
                lambda: CompanyFactory(
                    id='00000000-0000-0000-0000-000000000000',
                    name='Name 1',
                    company_number='00000000',
                    duns_number=None,
                    address_postcode='W1',
                    reference_code='',
                ),
                {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'company_name': 'Name 1',
                    'companies_house_id': '00000000',
                    'postcode': 'W1',
                },
            ),
        ),
    )
    def _test_model_to_match_payload(
        self,
        requests_mock,
        build_company,
        expected_result,
    ):
        """
        Test that the function maps the Company object to JSON correctly
        also stripping out falsy values.
        """
        company = build_company()
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
        )
        match_id = 1
        matcher = requests_mock.post(
            f'/api/v1/wins/{match_id}/',
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )
        export_wins(company)

        assert matcher.called_once
        assert matcher.last_request.json() == {
            'descriptions': [expected_result],
        }

    @override_settings(EXPORT_WINS_SERVICE_BASE_URL=None)
    def test_export_wins_api_missing_settings_error(self):
        """
        Test when environment variables are not set an exception is thrown.
        """
        company = CompanyFactory()
        with pytest.raises(ImproperlyConfigured):
            export_wins(company)

    @pytest.mark.parametrize(
        'request_exception,expected_exception',
        (
            (
                ConnectionError,
                ExportWinsAPIConnectionError,
            ),
            (
                ConnectTimeout,
                ExportWinsAPIConnectionError,
            ),
            (
                Timeout,
                ExportWinsAPITimeoutError,
            ),
            (
                ReadTimeout,
                ExportWinsAPITimeoutError,
            ),
        ),
    )
    def test_export_wins_api_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
    ):
        """
        Test if there is an error connecting to export wins API
        the expected exception was thrown.
        """
        match_id = 1
        requests_mock.post(
            f'/api/v1/wins/{match_id}/',
            exc=request_exception,
        )
        company = CompanyFactory()
        with pytest.raises(expected_exception):
            export_wins(company)

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ),
    )
    def test_export_wins_api_error(
        self,
        requests_mock,
        response_status,
    ):
        """Test if the export wins api returns a status code that is not 200."""
        match_id = 1
        requests_mock.post(
            f'/api/v1/wins/{match_id}/',
            status_code=response_status,
        )
        company = CompanyFactory()
        with pytest.raises(
            ExportWinsAPIHTTPError,
            match=f'The Export Wins API returned an error status: {response_status}',
        ):
            export_wins(company)
