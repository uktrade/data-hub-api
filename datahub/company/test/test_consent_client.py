import pytest
from django.conf import settings
from requests.exceptions import ConnectionError, HTTPError, Timeout
from rest_framework import status

from datahub.company import consent as consent
from datahub.company.constants import CONSENT_SERVICE_EMAIL_CONSENT_TYPE
from datahub.core.test_utils import HawkMockJSONResponse


def generate_hawk_response(json):
    """Mocks HAWK server validation for content."""
    return HawkMockJSONResponse(
        api_id=settings.COMPANY_MATCHING_HAWK_ID,
        api_key=settings.COMPANY_MATCHING_HAWK_KEY,
        response=json,
    )


class TestConsentClient:
    """
    Test for consent service client module
    """

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_get_one(self, requests_mock, accepts_marketing):
        """
        Try to get consent status for a single email address
        """
        matcher = requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            text=generate_hawk_response({
                'results': [{
                    'email': 'foo@bar.com',
                    'consents': [
                        CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                    ] if accepts_marketing else [],
                }],
            }),
            status_code=status.HTTP_200_OK,
        )
        resp = consent.get_one('foo@bar.com')
        assert resp == accepts_marketing

        assert matcher.called_once
        assert matcher.last_request.query == 'limit=1'
        assert matcher.last_request.json() == {'emails': ['foo@bar.com']}

    @pytest.mark.parametrize('emails', ([], ['foo@bar.com'], ['bar@foo.com', 'foo@bar.com']))
    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_get_many(self, requests_mock, accepts_marketing, emails):
        """
        Try to get consent status for a list of email addresses
        """
        matcher = requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            text=generate_hawk_response({
                'results': [
                    {
                        'email': email,
                        'consents': [
                            CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                        ] if accepts_marketing else [],
                    } for email in emails
                ],
            }),
            status_code=status.HTTP_200_OK,
        )
        resp = consent.get_many(emails)
        assert resp == {email: accepts_marketing for email in emails}

        assert matcher.called_once
        assert matcher.last_request.query == f'limit={len(emails)}'
        assert matcher.last_request.json() == {'emails': emails}

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_update(self, requests_mock, accepts_marketing):
        """
        Try to update consent status
        """
        matcher = requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH}',
            text=generate_hawk_response({
                'consents': [
                    CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                ],
                'modified_at': '2020-03-12T15:33:50.907000Z',
                'email': 'foo@bar.com',
                'phone': '',
                'key_type': 'email',
            }),
            status_code=status.HTTP_201_CREATED,
        )
        result = consent.update_consent('foo@bar.com', accepts_marketing)
        assert result is None
        assert matcher.called_once

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ),
    )
    def test_get_one_consent_is_false_when_service_5xx_errors(
            self,
            requests_mock,
            response_status,
    ):
        """
        When the Consent Service is down with a 5XX error,
        It returns an email with false as the value.
        """
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )
        response = consent.get_one('foo@bar.com')
        assert response is False

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ),
    )
    def test_get_many_consent_is_false_when_service_5xx_errors(
        self,
        requests_mock,
        response_status,
    ):
        """
        When the Consent Service is down with a 5XX error,
        It returns a dictionary of emails with false as their values.
        """
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )
        emails = ['foo1@bar.com', 'foo2@bar.com', 'foo3@bar.com']
        response = consent.get_many(emails)
        assert response == {email: False for email in emails}

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
    )
    def test_get_one_raises_exception_when_service_4xx_errors(
        self,
        requests_mock,
        response_status,
    ):
        """
        When the Consent Service responds with a 4XX error, It raises a HTTPError.
        """
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )

        with pytest.raises(HTTPError):
            consent.get_one('foo@bar.com')

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ),
    )
    def test_get_many_raises_exception_when_service_4xx_errors(
        self,
        requests_mock,
        response_status,
    ):
        """
        When the Consent Service responds with a 4XX error, It raises a HTTPError.
        """
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )
        emails = ['foo1@bar.com', 'foo2@bar.com', 'foo3@bar.com']
        with pytest.raises(HTTPError):
            consent.get_many(emails)

    @pytest.mark.parametrize(
        'request_exception',
        (
            ConnectionError,
            Timeout,
        ),
    )
    def test_get_many_raises_exception_on_connection_or_timeout_error(
        self,
        requests_mock,
        request_exception,
    ):
        """
        When the Consent Service responds with a 4XX error, It raises
        a ConnectionError or a Timeout Error
        """
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            exc=request_exception,
        )
        emails = ['foo1@bar.com', 'foo2@bar.com', 'foo3@bar.com']
        with pytest.raises(request_exception):
            consent.get_many(emails)

    @pytest.mark.parametrize(
        'request_exception',
        (
            ConnectionError,
            Timeout,
        ),
    )
    def test_get_one_raises_exception_on_connection_or_timeout_error(
        self,
        requests_mock,
        request_exception,
    ):
        """
        When the Consent Service responds with a 4XX error, It raises
        a ConnectionError or a Timeout Error
        """
        requests_mock.post(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            exc=request_exception,
        )
        with pytest.raises(request_exception):
            consent.get_one('foo@bar.com')
