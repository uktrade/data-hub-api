from unittest import mock
from uuid import UUID

import pytest
from django.core.management.sql import emit_post_migrate_signal
from django.db import DEFAULT_DB_ALIAS

from datahub.company.constants import (
    BusinessTypeConstant,
    NOTIFY_DNB_INVESTIGATION_FEATURE_FLAG,
)
from datahub.company.test.factories import CompanyFactory
from datahub.feature_flag.test.factories import FeatureFlagFactory
from datahub.metadata.models import BusinessType
from datahub.notification.core import notify_gateway

pytestmark = pytest.mark.django_db


class TestCompanyBusinessTypePostMigrate:
    """
    Tests for the `company_business_type_post_migrate` signal receiver.
    """

    def test_db_in_sync(self):
        """
        Test that business types have been correctly loaded.
        """
        loaded_business_types = {
            (obj.id, obj.name) for obj in BusinessType.objects.all()
        }
        expected_business_types = {
            (UUID(obj.value.id), obj.value.name)
            for obj in BusinessTypeConstant
        }
        assert loaded_business_types == expected_business_types

    @mock.patch('datahub.company.signals.load_constants_to_database')
    def test_only_called_once(self, mocked_load_constants_to_database):
        """
        Test that load_constants_to_database is only called once.
        """
        emit_post_migrate_signal(verbosity=1, interactive=False, db=DEFAULT_DB_ALIAS)
        mocked_load_constants_to_database.assert_called_once()


class TestNotifyDNBInvestigation:
    """
    Test the `notify_dnb_investigation` signal is triggered appropriately.
    """

    def _get_dnb_investigation_notify_client(self):
        FeatureFlagFactory(code=NOTIFY_DNB_INVESTIGATION_FEATURE_FLAG, is_active=True)
        client = notify_gateway.clients['dnb_investigation']
        client.reset_mock()
        return client

    def test_notify_signal_pending_investigation(self):
        """
        Test that a notification would be sent when a company is created which
        is pending DNB investigation.
        """
        client = self._get_dnb_investigation_notify_client()
        CompanyFactory(pending_dnb_investigation=True)
        client.send_email_notification.assert_called()

    def test_notify_signal_company_not_pending_no_investigation(self):
        """
        Test that a notification would not be sent when a company is created which
        is not pending investigation.
        """
        client = self._get_dnb_investigation_notify_client()
        CompanyFactory(pending_dnb_investigation=False)
        client.send_email_notification.assert_not_called()

    def test_notify_signal_company_updated_no_investigation(self):
        """
        Test that a notification would not be sent when a company pending investigation
        is updated.
        """
        client = self._get_dnb_investigation_notify_client()
        company = CompanyFactory(pending_dnb_investigation=True)
        client.reset_mock()
        company.name = 'foobar'
        company.save()
        client.send_email_notification.assert_not_called()
