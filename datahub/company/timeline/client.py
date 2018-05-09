from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from raven.contrib.django.models import client
from requests import HTTPError
from rest_framework import status
from rest_framework.exceptions import APIException

from datahub.company.timeline.exceptions import InvalidCompanyNumberError
from datahub.company.timeline.serializers import TimelineEventSerializer
from datahub.core.api_client import APIClient, HawkAuth


class ReportingServiceClient:
    """
    DT07 reporting service client.

    (See https://github.com/uktrade/dt07-reporting for more information on the reporting service.)

    This is used for retrieving company timeline data.
    """

    def __init__(self):
        """
        Initialises the client.

        The API URL and key are taken from settings.
        """
        api_url = settings.REPORTING_SERVICE_API_URL
        api_id = settings.REPORTING_SERVICE_API_ID
        api_key = settings.REPORTING_SERVICE_API_KEY

        if not all((api_url, api_id, api_key)):
            raise ImproperlyConfigured('Reporting service connection details not configured')

        timeout = settings.REPORTING_SERVICE_API_TIMEOUT
        verify_responses = settings.REPORTING_SERVICE_API_VERIFY_RESPONSES

        auth = HawkAuth(api_id, api_key, verify_response=verify_responses)
        self._api_client = APIClient(api_url, auth, default_timeout=timeout)

    def get_timeline_events_by_company_number(self, company_number):
        """Gets timeline events for a company using a company number."""
        transformed_company_number = _transform_company_number(company_number)
        if not transformed_company_number:
            raise InvalidCompanyNumberError

        data = self._request('/api/v1/company/events/', params={
            'companies_house_id': transformed_company_number,
        })

        serializer = TimelineEventSerializer(data=data.get('events', []), many=True)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _request(self, path, **kwargs):
        try:
            response = self._api_client.request('get', path, **kwargs)
        except HTTPError as exc:
            if exc.response.status_code != status.HTTP_404_NOT_FOUND:
                event_id = client.captureException()
                raise APIException(f'Error communicating with the company timeline API. Error '
                                   f'reference: {event_id}.') from exc
            return {}
        else:
            return response.json()


def _transform_company_number(company_number):
    """
    This ensures that the company_number is a string and removes any leading zeroes.

    The latter is required as the reporting service does not return results for
    company numbers that start with a leading zero unless the leading zeroes are removed.
    """
    transformed_company_number = company_number or ''
    transformed_company_number = transformed_company_number.lstrip('0')
    return transformed_company_number
