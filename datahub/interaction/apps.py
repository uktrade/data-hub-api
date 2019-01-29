from datetime import timedelta
from logging import getLogger

from django.apps import AppConfig
from django.conf import settings
from django.core.cache import cache


logger = getLogger(__name__)
MIGRATE_CONTACTS_CACHE_KEY = 'dbmaintenance_migrate_interaction_contacts'
MIGRATE_CONTACTS_CACHE_KEY_EXPIRY = int(timedelta(hours=6).total_seconds())


class InteractionConfig(AppConfig):
    """Configuration class for this app."""

    name = 'datahub.interaction'

    def ready(self):
        """Schedules a task to populate Interactions.contacts from Interaction.contact."""
        from datahub.dbmaintenance.tasks import copy_foreign_key_to_m2m_field

        if not settings.ENABLE_APP_READY_DATA_MIGRATIONS:
            return

        key_was_set = cache.add(MIGRATE_CONTACTS_CACHE_KEY, 1, MIGRATE_CONTACTS_CACHE_KEY_EXPIRY)
        if key_was_set:
            copy_foreign_key_to_m2m_field.apply_async(
                args=('interaction.Interaction', 'contact', 'contacts'),
                countdown=settings.APP_READY_DATA_MIGRATION_DELAY_SECS,
            )
