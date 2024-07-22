import urllib.parse

import pytest
from django.conf import settings
from requests.exceptions import ConnectionError, Timeout
from rest_framework import status

from datahub.company import consent as consent
from datahub.company.constants import CONSENT_SERVICE_EMAIL_CONSENT_TYPE
from datahub.core.test_utils import HawkMockJSONResponse


def generate_hawk_response(payload):
    """Mocks HAWK server validation for content."""
    return HawkMockJSONResponse(
        api_id=settings.CONSENT_SERVICE_HAWK_ID,
        api_key=settings.CONSENT_SERVICE_HAWK_KEY,
        response=payload,
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
        matcher = requests_mock.get(
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
        assert matcher.last_request.query == 'email=foo%40bar.com'

    @pytest.mark.parametrize('emails', ([], ['foo@bar.com'], ['bar@foo.com', 'foo@bar.com']))
    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_get_many(self, requests_mock, accepts_marketing, emails):
        """
        Try to get consent status for a list of email addresses
        """
        matcher = requests_mock.get(
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
        assert matcher.last_request.query == urllib.parse.urlencode({'email': emails}, doseq=True)

    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_get_one_normalises_emails(self, requests_mock, accepts_marketing):
        """
        Try to get consent status for a single email address
        """
        matcher = requests_mock.get(
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
        resp = consent.get_one('FOO@BAR.COM')
        assert resp == accepts_marketing

        assert matcher.called_once
        assert matcher.last_request.query == 'email=foo%40bar.com'

    @pytest.mark.parametrize('emails', ([], ['foo@bar.com'], ['bar@foo.com', 'foo@bar.com']))
    @pytest.mark.parametrize('accepts_marketing', (True, False))
    def test_get_many_normalises_emails(self, requests_mock, accepts_marketing, emails):
        """
        Try to get consent status for a list of email addresses
        """
        matcher = requests_mock.get(
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
        resp = consent.get_many([email.upper() for email in emails])
        assert resp == {email: accepts_marketing for email in emails}

        assert matcher.called_once
        assert matcher.last_request.query == urllib.parse.urlencode({'email': emails}, doseq=True)

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

    def test_forward_zipkin_headers(self, requests_mock):
        """
        Forward zipkin headers from origin request to the API call
        """
        headers = {
            'x-b3-traceid': '123',
            'x-b3-spanid': '456',
        }
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
        result = consent.update_consent('foo@bar.com', False, None,
                                        headers=headers)
        assert result is None
        assert headers.items() <= matcher.last_request.headers.items()
        assert matcher.called_once

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ),
    )
    def test_get_one_raises_exception_when_service_http_errors(
        self,
        requests_mock,
        response_status,
    ):
        """
        When the Consent Service responds with a http error, It raises a HTTPError.
        """
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )

        with pytest.raises(consent.ConsentAPIHTTPError):
            consent.get_one('foo@bar.com')

    @pytest.mark.parametrize(
        'response_status',
        (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_502_BAD_GATEWAY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT,
        ),
    )
    def test_get_many_raises_exception_when_service_http_errors(
        self,
        requests_mock,
        response_status,
    ):
        """
        When the Consent Service responds with a http error, It raises a HTTPError.
        """
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            status_code=response_status,
        )
        emails = ['foo1@bar.com', 'foo2@bar.com', 'foo3@bar.com']
        with pytest.raises(consent.ConsentAPIHTTPError):
            consent.get_many(emails)

    @pytest.mark.parametrize(
        'exceptions',
        (
            (ConnectionError, consent.ConsentAPIConnectionError),
            (Timeout, consent.ConsentAPITimeoutError),
        ),
    )
    def test_get_many_raises_exception_on_connection_or_timeout_error(
        self,
        requests_mock,
        exceptions,
    ):
        """
        When the Consent Service responds with a 4XX error, It raises
        a ConnectionError or a Timeout Error
        """
        (request_exception, consent_exception) = exceptions
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            exc=request_exception,
        )
        emails = ['foo1@bar.com', 'foo2@bar.com', 'foo3@bar.com']
        with pytest.raises(consent_exception):
            consent.get_many(emails)

    @pytest.mark.parametrize(
        'exceptions',
        (
            (ConnectionError, consent.ConsentAPIConnectionError),
            (Timeout, consent.ConsentAPITimeoutError),
        ),
    )
    def test_get_one_raises_exception_on_connection_or_timeout_error(
        self,
        requests_mock,
        exceptions,
    ):
        """
        When the Consent Service responds with a 4XX error, It raises
        a ConnectionError or a Timeout Error
        """
        (request_exception, consent_exception) = exceptions
        requests_mock.get(
            f'{settings.CONSENT_SERVICE_BASE_URL}'
            f'{consent.CONSENT_SERVICE_PERSON_PATH_LOOKUP}',
            exc=request_exception,
        )
        with pytest.raises(consent_exception):
            consent.get_one('foo@bar.com')
