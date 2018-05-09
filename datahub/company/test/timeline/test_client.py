from datetime import datetime
from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import utc
from rest_framework import status
from rest_framework.exceptions import APIException

from datahub.company.timeline.client import ReportingServiceClient
from datahub.company.timeline.exceptions import InvalidCompanyNumberError

FAKE_RESPONSES = {
    '/api/v1/company/events/?companies_house_id=125694': {
        'json': {
            'events': [{
                'data_source': 'companies_house.companies',
                'datetime': 'Mon, 31 Dec 2018 00:00:00 GMT',
                'description': 'Accounts next due date',
            }, {
                'data_source': 'companies_house.companies',
                'datetime': 'Mon, 31 Dec 2017 00:00:00 GMT',
                'description': 'Accounts filed',
            }]
        }
    },
    '/api/v1/company/events/?companies_house_id=356812': {
        'status_code': status.HTTP_404_NOT_FOUND
    },
    '/api/v1/company/events/?companies_house_id=886423': {
        'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
    },
}


class TestReportingServiceClient:
    """Tests the reporting service client."""

    @pytest.fixture(autouse=True)
    def fake_api(self, requests_stubber):
        """Fixture that stubs the reporting service."""
        for path, kwargs in FAKE_RESPONSES.items():
            url = urljoin(settings.REPORTING_SERVICE_API_URL, path)
            requests_stubber.get(url, **kwargs)

    @pytest.mark.parametrize(
        'api_url,api_id,api_key',
        (
            ('', 'api-id', 'api-key'),
            ('api-url', '', 'api-key'),
            ('api-url', 'api-id', ''),
        )
    )
    def test_raises_an_error_on_invalid_configuration(self, monkeypatch, api_url, api_id, api_key):
        """Test that ImproperlyConfigured if the API connection details are not configured."""
        monkeypatch.setattr(settings, 'REPORTING_SERVICE_API_URL', api_url)
        monkeypatch.setattr(settings, 'REPORTING_SERVICE_API_ID', api_id)
        monkeypatch.setattr(settings, 'REPORTING_SERVICE_API_KEY', api_key)

        with pytest.raises(ImproperlyConfigured):
            ReportingServiceClient()

    @pytest.mark.parametrize('company_number', (None, '', '00', ))
    def test_raises_an_error_on_blank_like_company_numbers(self, company_number):
        """Test that an error is raised for company numbers that are blank or only zeroes."""
        client = ReportingServiceClient()

        with pytest.raises(InvalidCompanyNumberError):
            client.get_timeline_events_by_company_number(company_number)

    def test_returns_an_empty_list_on_non_existent_company_number(self):
        """Test that an empty list of events is returned for a non-existent company number."""
        client = ReportingServiceClient()
        assert client.get_timeline_events_by_company_number('356812') == []

    def test_raises_api_exception_on_api_error(self):
        """Test that an APIException is raised when a 500 is returned by the API."""
        client = ReportingServiceClient()

        with pytest.raises(APIException):
            client.get_timeline_events_by_company_number('886423')

    @pytest.mark.parametrize('company_number', ('0125694', '125694'))
    def test_transforms_the_api_response(self, company_number):
        """Test the re-formatting of the API response."""
        client = ReportingServiceClient()
        assert client.get_timeline_events_by_company_number(company_number) == [{
            'data_source': 'companies_house.companies',
            'datetime': datetime(2018, 12, 31, tzinfo=utc),
            'description': 'Accounts next due date',
        }, {
            'data_source': 'companies_house.companies',
            'datetime': datetime(2017, 12, 31, tzinfo=utc),
            'description': 'Accounts filed',
        }]
