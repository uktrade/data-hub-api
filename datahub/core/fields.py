from django.db.models import CharField


class CICharField(CharField):
    """Case insensitive Postgres CharField.

    This is a backport from Django 1.11. Delete this field when Django is upgraded.
    """

    def db_type(self, connection):
        """Define db type."""
        return 'citext'
