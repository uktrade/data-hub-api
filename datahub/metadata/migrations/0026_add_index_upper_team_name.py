"""
Creates an index on UPPER(name) on the Team model (for use with the
iexact filter look-up).

As Django does not support creating indexes on expressions, SQL is used.

The migration is run inside a transaction, so CREATE INDEX CONCURRENTLY is not used.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0025_update_sector_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                '''CREATE INDEX "metadata_team_upper_name_ed973c5a"
ON "metadata_team" (UPPER("name"));'''
            ],
            reverse_sql=['DROP INDEX "metadata_team_upper_name_ed973c5a";'],
        ),
    ]
