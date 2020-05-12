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
    ExportWinsAPIConnectionError,
    ExportWinsAPIHTTPError,
    ExportWinsAPITimeoutError,
    get_export_wins,
)
from datahub.core.test_utils import APITestMixin, HawkMockJSONResponse


class TestExportWinsApi(APITestMixin):
    """
    Tests functionality to obtain export wins for a company,
    first by getting match if with a post to the company matching service
    and then getting export wins for from export wins API and error handling.
    """

    @override_settings(EXPORT_WINS_SERVICE_BASE_URL=None)
    def test_export_wins_api_missing_settings_error(self):
        """
        Test when environment variables are not set an exception is thrown.
        """
        with pytest.raises(ImproperlyConfigured):
            get_export_wins([1234])

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
        match_id = 1234
        requests_mock.get(
            f'/wins/match?match_id={match_id}',
            exc=request_exception,
        )
        with pytest.raises(expected_exception):
            get_export_wins([match_id])

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
        requests_mock.get(
            f'/wins/match?match_id={match_id}',
            status_code=response_status,
        )
        with pytest.raises(
            ExportWinsAPIHTTPError,
            match=f'The Export Wins API returned an error status: {response_status}',
        ):
            get_export_wins([match_id])

    def test_get_call_invoked_one_match_id(
        self,
        requests_mock,
    ):
        """
        Check GET call will be made
        """
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
        )
        match_id = 1234
        matcher = requests_mock.get(
            f'/wins/match?match_id={match_id}',
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )
        get_export_wins([match_id])

        assert matcher.called_once

    def test_get_call_invoked_multiple_match_ids(
        self,
        requests_mock,
    ):
        """
        Check GET call will be made
        """
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
        )
        matcher = requests_mock.get(
            f'/wins/match?match_id=1234,2345',
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )
        get_export_wins([1234, 2345])

        assert matcher.called_once
