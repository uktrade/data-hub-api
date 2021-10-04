from django.core.management import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS
from django_pglocks import advisory_lock


class AppLabelAlreadyRenamedError(CommandError):
    """Error raised when new app_label or app is found when executing rename_apps command."""


class Command(BaseCommand):
    """Renames django app labels."""

    apps_to_rename = [
        ('omis_invoice', 'omis-invoice'),
        ('omis_quote', 'omis-quote'),
        ('omis_market', 'omis-market'),
        ('omis_payment', 'omis-payment'),
        ('omis_region', 'omis-region'),
    ]

    def add_arguments(self, parser):
        """Add arguments."""
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )
        parser.add_argument(
            '--skip-content-type', '--sct',
            action='store_true',
            default=False,
            help='Skip django_content_type from renaming.',
        )

    def handle(self, *args, **options):
        """Execute command."""
        with advisory_lock('apps_migration'):
            database = options['database']
            connection = connections[database]

            for app in self.apps_to_rename:
                self.rename_app(
                    connection,
                    app[1],
                    app[0],
                    skip_content_type=options['skip_content_type'],
                )

    def rename_app(self, connection, old_app_label, new_app_label, skip_content_type=False):
        """Rename app."""
        with connection.cursor() as cursor:
            if not skip_content_type:
                # Remote database, like `mi`, may not have a `django_content_type` table.
                cursor.execute(
                    'SELECT app_label FROM django_content_type WHERE app_label=%s',
                    (new_app_label,),
                )
                exists = cursor.fetchone()
                if exists:
                    raise AppLabelAlreadyRenamedError(
                        'Cannot run rename_apps for django_content_type new app_label already '
                        f'exists. Existing app_label found: {new_app_label}.',
                    )
                    return

                cursor.execute(
                    'UPDATE django_content_type SET app_label=%s WHERE app_label=%s',
                    (new_app_label, old_app_label),
                )

            cursor.execute(
                'SELECT app FROM django_migrations WHERE app=%s',
                (new_app_label,),
            )
            exists = cursor.fetchone()
            if exists:
                raise AppLabelAlreadyRenamedError(
                    'Cannot run rename_apps for django_migrations as new app already exists. '
                    f'Existing app found: {new_app_label}.',
                )
                return

            cursor.execute(
                'UPDATE django_migrations SET app=%s WHERE app=%s',
                (new_app_label, old_app_label),
            )
