import logging
from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from requests import ConnectTimeout
from rest_framework import status

from datahub.company.constants import UPDATE_CONSENT_SERVICE_FEATURE_FLAG
from datahub.company.tasks import update_contact_consent
from datahub.feature_flag.test.factories import FeatureFlagFactory


@pytest.fixture()
def update_consent_service_feature_flag():
    """
    Creates the consent service feature flag.
    """
    yield FeatureFlagFactory(code=UPDATE_CONSENT_SERVICE_FEATURE_FLAG)


@pytest.mark.django_db
class TestConsentServiceTask:
    """
    tests for the task that sends email marketing consent status to the
    DIT consent service / legal basis API
    """

    def test_no_feature_flag(
            self,
            caplog,
    ):
        """
        Test that if the feature flag is not enabled, the
        task will not run.
        """
        caplog.set_level(logging.INFO, logger='datahub.company.tasks.contact')
        update_contact_consent.apply_async(args=('example@exmaple.com', True))
        assert caplog.messages == [
            f'Feature flag "{UPDATE_CONSENT_SERVICE_FEATURE_FLAG}" is not active, exiting.',
        ]

    @override_settings(
        CONSENT_SERVICE_BASE_URL=None,
    )
    def test_with_flag_but_not_configured(
            self,
            update_consent_service_feature_flag,
    ):
        """
        Test that if feature flag is enabled, but environment variables are not set
        then task will throw exception
        """
        with pytest.raises(ImproperlyConfigured):
            update_contact_consent('example@example.com', True)

    @pytest.mark.parametrize(
        'email_address, accepts_dit_email_marketing, modified_at',
        (
            ('example@example.com', True, None),
            ('example@example.com', False, None),
            ('example@example.com', True, '2020-01-01-12:00:00Z'),
            ('example@example.com', False, '2020-01-01-12:00:00Z'),
        ),
    )
    def test_task_makes_http_request(
            self,
            update_consent_service_feature_flag,
            requests_mock,
            email_address,
            accepts_dit_email_marketing,
            modified_at,
    ):
        """
        Ensure correct http request with correct payload is generated when task
        executes.
        """
        matcher = requests_mock.post('/api/v1/person/', json={},
                                     status_code=status.HTTP_201_CREATED)
        update_contact_consent(
            email_address,
            accepts_dit_email_marketing,
            modified_at=modified_at,
        )
        assert matcher.called_once
        expected = {
            'email': email_address,
            'consents': ['email_marketing'] if accepts_dit_email_marketing else [],
        }
        if modified_at:
            expected['modified_at'] = modified_at

        assert matcher.last_request.json() == expected

    @pytest.mark.parametrize(
        'status_code',
        (
            (status.HTTP_404_NOT_FOUND),
            (status.HTTP_403_FORBIDDEN),
            (status.HTTP_500_INTERNAL_SERVER_ERROR),
        ),
    )
    @patch('datahub.company.tasks.contact.update_contact_consent.retry', side_effect=Retry)
    def test_task_retries_on_request_exceptions(
            self,
            mock_retry,
            update_consent_service_feature_flag,
            requests_mock,
            status_code,
    ):
        """
        Test to ensure that celery retries on request exceptions like 5xx, 404
        """
        matcher = requests_mock.post('/api/v1/person/', json={}, status_code=status_code)
        with pytest.raises(Retry):
            update_contact_consent('example@example.com', True)
        assert matcher.called_once
        assert mock_retry.call_args.kwargs['exc'].response.status_code == status_code

    @patch('datahub.company.tasks.contact.update_contact_consent.retry', side_effect=Retry)
    @patch('datahub.company.consent.APIClient.request', side_effect=ConnectTimeout)
    def test_task_retries_on_connect_timeout(
            self,
            mock_post,
            mock_retry,
            update_consent_service_feature_flag,
    ):
        """
        Test to ensure that celery retries on connect timeout
        """
        with pytest.raises(Retry):
            update_contact_consent('example@example.com', True)
        assert mock_post.called
        assert isinstance(mock_retry.call_args.kwargs['exc'], ConnectTimeout)

    @patch('datahub.company.tasks.contact.update_contact_consent.retry', side_effect=Retry)
    @patch('datahub.company.consent.APIClient.request', side_effect=Exception)
    def test_task_doesnt_retry_on_other_exception(
            self,
            mock_post,
            mock_retry,
            update_consent_service_feature_flag,
    ):
        """
        Test to ensure that celery raises on non-requests exception
        """
        with pytest.raises(Exception):
            update_contact_consent('example@example.com', True)
        assert mock_post.called
        assert not mock_retry.called
