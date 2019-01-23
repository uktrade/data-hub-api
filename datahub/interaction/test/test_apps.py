from unittest.mock import Mock

import pytest
from django.test import override_settings

from datahub.interaction.apps import InteractionConfig


@override_settings(ENABLE_APP_READY_DATA_MIGRATIONS=True)
@pytest.mark.usefixtures('local_memory_cache')
def test_schedules_contacts_migration(monkeypatch):
    """Test that copy_foreign_key_to_m2m_field_mock is scheduled once on app ready."""
    copy_foreign_key_to_m2m_field_mock = Mock()
    monkeypatch.setattr(
        'datahub.dbmaintenance.tasks.copy_foreign_key_to_m2m_field',
        copy_foreign_key_to_m2m_field_mock,
    )

    InteractionConfig.ready(None)
    copy_foreign_key_to_m2m_field_mock.apply_async.assert_called_once()

    # Should not be started a second time if ready() called again
    copy_foreign_key_to_m2m_field_mock.apply_async.reset_mock()
    InteractionConfig.ready(None)
    copy_foreign_key_to_m2m_field_mock.apply_async.assert_not_called()
