import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from freezegun import freeze_time
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    ReadTimeout,
    Timeout,
)
from rest_framework import status

from datahub.company.company_matching_api import (
    bulk_match_not_matched_companies,
    CompanyMatchingServiceConnectionError,
    CompanyMatchingServiceHTTPError,
    CompanyMatchingServiceTimeoutError,
    match_company,
)
from datahub.company.models import Company
from datahub.company.test.factories import CompanyFactory, DuplicateCompanyFactory
from datahub.core.test_utils import APITestMixin, HawkMockJSONResponse


class TestCompanyMatchingApi(APITestMixin):
    """
    Tests Company matching API functionality including formating a Company Object
    to JSON to post to the company matching service and error handling.
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
    def test_model_to_match_payload(
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
            api_id=settings.COMPANY_MATCHING_HAWK_ID,
            api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        )
        matcher = requests_mock.post(
            '/api/v1/company/match/',
            status_code=status.HTTP_200_OK,
            text=dynamic_response,
        )
        match_company([company])

        assert matcher.called_once
        assert matcher.last_request.json() == {
            'descriptions': [expected_result],
        }

    @override_settings(COMPANY_MATCHING_SERVICE_BASE_URL=None)
    def test_missing_settings_error(self):
        """
        Test when environment variables are not set an exception is thrown.
        """
        company = CompanyFactory()
        with pytest.raises(ImproperlyConfigured):
            match_company([company])

    @pytest.mark.parametrize(
        'request_exception,expected_exception',
        (
            (
                ConnectionError,
                CompanyMatchingServiceConnectionError,
            ),
            (
                ConnectTimeout,
                CompanyMatchingServiceConnectionError,
            ),
            (
                Timeout,
                CompanyMatchingServiceTimeoutError,
            ),
            (
                ReadTimeout,
                CompanyMatchingServiceTimeoutError,
            ),
        ),
    )
    def test_company_matching_service_request_error(
        self,
        requests_mock,
        request_exception,
        expected_exception,
    ):
        """
        Test if there is an error connecting to company matching service
        the expected exception was thrown.
        """
        requests_mock.post(
            '/api/v1/company/match/',
            exc=request_exception,
        )
        company = CompanyFactory()
        with pytest.raises(expected_exception):
            match_company([company])

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
    def test_company_matching_service_error(
        self,
        requests_mock,
        response_status,
    ):
        """Test if the company matching service returns a status code that is not 200."""
        requests_mock.post(
            '/api/v1/company/match/',
            status_code=response_status,
        )
        company = CompanyFactory()
        with pytest.raises(
            CompanyMatchingServiceHTTPError,
            match=f'The Company matching service returned an error status: {response_status}',
        ):
            match_company([company])


@pytest.mark.django_db
def test_bulk_match_not_matched_companies(requests_mock):
    """Test that result of match is stored with the company."""
    company_matching_reponse = {
        'matches': [
            {
                'id': 1,
                'match_id': match_id,
                'similarity': '100000',
            }
            for match_id in [1, 2]
        ],
    }

    dynamic_response = HawkMockJSONResponse(
        api_id=settings.COMPANY_MATCHING_HAWK_ID,
        api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        response=company_matching_reponse,
    )
    matcher = requests_mock.post(
        '/api/v1/company/match/',
        status_code=status.HTTP_200_OK,
        text=dynamic_response,
    )
    DuplicateCompanyFactory.create_batch(5)

    with freeze_time() as frozen_datetime:
        bulk_match_not_matched_companies(length=2)

        assert matcher.call_count == 2

        matched = Company.objects.filter(
            export_win_match_id=1,
            export_win_last_matched_on=frozen_datetime(),
        )
        assert matched.count() == 2


@pytest.mark.django_db
def test_bulk_match_not_matched_companies_no_match(requests_mock):
    """Test that last match date is set when there are no matches."""
    company_matching_reponse = {
        'matches': [],
    }

    dynamic_response = HawkMockJSONResponse(
        api_id=settings.COMPANY_MATCHING_HAWK_ID,
        api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        response=company_matching_reponse,
    )
    matcher = requests_mock.post(
        '/api/v1/company/match/',
        status_code=status.HTTP_200_OK,
        text=dynamic_response,
    )
    CompanyFactory.create_batch(5)

    with freeze_time() as frozen_datetime:
        bulk_match_not_matched_companies(length=2)

        assert matcher.call_count == 2

        matched = Company.objects.filter(
            export_win_match_id__isnull=True,
            export_win_last_matched_on=frozen_datetime(),
        )
        assert matched.count() == 2
