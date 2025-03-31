import time

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

from datahub.core.test_utils import APITestMixin, HawkMockJSONResponse
from datahub.export_win.export_wins_api import (
    ExportWinsAPIConnectionError,
    ExportWinsAPIHTTPError,
    ExportWinsAPITimeoutError,
    get_legacy_export_wins_dataset,
)


@pytest.fixture
def mock_sleep(monkeypatch):
    def sleep(seconds):
        pass
    monkeypatch.setattr(time, 'sleep', sleep)


class TestExportWinsDatasetApi(APITestMixin):
    """Tests functionality to obtain export wins datasets.
    """

    @override_settings(EXPORT_WINS_SERVICE_BASE_URL=None)
    def test_export_wins_api_missing_settings_error(self):
        """Test when environment variables are not set an exception is thrown.
        """
        with pytest.raises(ImproperlyConfigured):
            next(get_legacy_export_wins_dataset('/data-hub-wins'))

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
        mock_sleep,
    ):
        """Test if there is an error connecting to export wins API
        the expected exception was thrown.
        """
        requests_mock.get(
            '/data-hub-wins',
            exc=request_exception,
        )
        with pytest.raises(expected_exception):
            next(get_legacy_export_wins_dataset('/data-hub-wins'))

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
        mock_sleep,
    ):
        """Test if the export wins api returns a status code that is not 200."""
        requests_mock.get(
            '/data-hub-wins',
            status_code=response_status,
        )
        with pytest.raises(
            ExportWinsAPIHTTPError,
            match=f'The Export Wins API returned an error status: {response_status}',
        ):
            next(get_legacy_export_wins_dataset('/data-hub-wins'))

    def test_get_call_invoked(
        self,
        requests_mock,
    ):
        """Check GET call will be made
        """
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response={
                'next': None,
                'results': [],
            },
        )
        matcher = requests_mock.get(
            '/data-hub-wins',
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )
        next(get_legacy_export_wins_dataset('/data-hub-wins'))

        assert matcher.called_once

    def test_get_call_retries(
        self,
        requests_mock,
        mock_sleep,
    ):
        """Check GET call will be retried
        """
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response={
                'next': None,
                'results': [{'test': 'response'}],
            },
        )
        matcher = requests_mock.get(
            '/data-hub-wins',
            [
                {
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
                {
                    'status_code': status.HTTP_400_BAD_REQUEST,
                },
                {
                    'status_code': status.HTTP_200_OK,
                    'text': dynamic_response,
                },
            ],
        )
        response = next(get_legacy_export_wins_dataset('/data-hub-wins'))
        assert matcher.call_count == 3
        assert len(response) == 1
        assert response[0] == {'test': 'response'}

    def test_get_call_aborts(
        self,
        requests_mock,
        mock_sleep,
    ):
        """Check GET call will be aborted
        """
        dynamic_response = HawkMockJSONResponse(
            api_id=settings.EXPORT_WINS_HAWK_ID,
            api_key=settings.EXPORT_WINS_HAWK_KEY,
            response={
                'next': None,
                'results': [{'test': 'response'}],
            },
        )
        requests_mock.get(
            '/data-hub-wins',
            [
                {
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
                {
                    'status_code': status.HTTP_400_BAD_REQUEST,
                },
                {
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                },
                {
                    'status_code': status.HTTP_400_BAD_REQUEST,
                },
                {
                    'status_code': status.HTTP_400_BAD_REQUEST,
                },
                {
                    'status_code': status.HTTP_200_OK,
                    'text': dynamic_response,
                },
            ],
        )
        with pytest.raises(
            ExportWinsAPIHTTPError,
            match=f'The Export Wins API returned an error status: {status.HTTP_400_BAD_REQUEST}',
        ):
            next(get_legacy_export_wins_dataset('/data-hub-wins'))
