import sentry_sdk
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests import HTTPError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from datahub.company.timeline.exceptions import InvalidCompanyNumberError
from datahub.company.timeline.serializers import TimelineEventSerializer
from datahub.core.api_client import APIClient, HawkAuth


class DataScienceCompanyAPIClient:
    """
    Client for the data science DT07 reporting service.

    (See https://github.com/uktrade/dt07-reporting for more information.)

    This is used for retrieving company timeline data.
    """

    def __init__(self):
        """
        Initialises the client.

        The API URL and key are taken from settings.
        """
        api_url = settings.DATA_SCIENCE_COMPANY_API_URL
        api_id = settings.DATA_SCIENCE_COMPANY_API_ID
        api_key = settings.DATA_SCIENCE_COMPANY_API_KEY

        if not all((api_url, api_id, api_key)):
            raise ImproperlyConfigured(
                'Data science company API connection details not configured',
            )

        timeout = settings.DATA_SCIENCE_COMPANY_API_TIMEOUT
        verify_responses = settings.DATA_SCIENCE_COMPANY_API_VERIFY_RESPONSES

        auth = HawkAuth(api_id, api_key, verify_response=verify_responses)
        self._api_client = APIClient(api_url, auth, default_timeout=timeout)

    def get_timeline_events_by_company_number(self, company_number):
        """Gets timeline events for a company using a company number."""
        transformed_company_number = _transform_company_number(company_number)
        if not transformed_company_number:
            raise InvalidCompanyNumberError

        data = self._request(
            '/api/v1/company/events/',
            params={
                'companies_house_id': transformed_company_number,
            },
        )

        return _transform_events_response(data)

    def _request(self, path, **kwargs):
        try:
            response = self._api_client.request('get', path, **kwargs)
        except HTTPError as exc:
            if exc.response.status_code != status.HTTP_404_NOT_FOUND:
                event_id = sentry_sdk.capture_exception()
                raise APIException(
                    f'Error communicating with the company timeline API. Error '
                    f'reference: {event_id}.',
                ) from exc
            return {}
        else:
            return response.json()


def _transform_events_response(data):
    serializer = TimelineEventSerializer(data=data.get('events', []), many=True)
    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError as exc:
        event_id = sentry_sdk.capture_exception()
        raise APIException(
            f'Unexpected response data format received from the company '
            f'timeline API. Error reference: {event_id}.',
        ) from exc

    return serializer.validated_data


def _transform_company_number(company_number):
    """
    This ensures that the company_number is a string and removes any leading zeroes.

    The latter is required as the upstream company timeline API does not return results for
    company numbers that start with a leading zero unless the leading zeroes are removed.
    """
    transformed_company_number = company_number or ''
    transformed_company_number = transformed_company_number.lstrip('0')
    return transformed_company_number
