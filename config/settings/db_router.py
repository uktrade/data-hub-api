from django.conf import settings


class DBRouter:
    """DBRouter to match models with their corresponding databases."""

    MI_DATABASE_LABEL = 'mi'

    def _db_for_read_and_write(self, model, **hints):
        if model._meta.app_config.name in settings.MI_APPS:
            return self.MI_DATABASE_LABEL
        return 'default'

    def db_for_read(self, model, **hints):
        """Return the database to read."""
        return self._db_for_read_and_write(model, **hints)

    def db_for_write(self, model, **hints):
        """Return the database to write."""
        return self._db_for_read_and_write(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        """Check if relation is allowed."""
        obj1_is_mi = obj1._meta.app_config.name in settings.MI_APPS
        obj2_is_mi = obj2._meta.app_config.name in settings.MI_APPS
        return obj1_is_mi == obj2_is_mi

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Check if given migration can be run against given database."""
        if db == self.MI_DATABASE_LABEL and app_label in settings.MI_APPS:
            return True

        return db == 'default' and app_label not in settings.MI_APPS
