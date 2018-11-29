from unittest import mock
from uuid import UUID

import pytest
from django.core.management.sql import emit_post_migrate_signal
from django.db import DEFAULT_DB_ALIAS

from datahub.company.constants import BusinessTypeConstant
from datahub.metadata.models import BusinessType

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
