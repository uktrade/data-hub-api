import pytest
from django.conf import settings
from rest_framework import status

from datahub.company import consent as consent
from datahub.company.constants import CONSENT_SERVICE_EMAIL_CONSENT_TYPE


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
            json={
                'results': [
                    {
                        'email': 'foo@bar.com',
                        'consents': [
                            CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                        ] if accepts_marketing else [],
                    },
                ],
            },
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
            json={
                'results': [
                    {
                        'email': email,
                        'consents': [
                            CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                        ] if accepts_marketing else [],
                    } for email in emails
                ],
            },
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
            json={
                'consents': [
                    CONSENT_SERVICE_EMAIL_CONSENT_TYPE,
                ],
                'modified_at': '2020-03-12T15:33:50.907000Z',
                'email': 'foo@bar.com',
                'phone': '',
                'key_type': 'email',
            },
            status_code=status.HTTP_201_CREATED,
        )
        result = consent.update_consent('foo@bar.com', accepts_marketing)
        assert result is None
        assert matcher.called_once
