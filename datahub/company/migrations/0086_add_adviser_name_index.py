"""
Creates an index on `("is_active", (UPPER("first_name" || ' ' || "last_name" )))` on
the Advisor model.

As Django does not support creating indexes on expressions, SQL is used.

The migration is run inside a transaction, so CREATE INDEX CONCURRENTLY is not used.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0085_remove_trading_address_from_db'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                '''CREATE INDEX "company_advisor_is_active_upper_name_e0ab1b4f"
ON "company_advisor" ("is_active", (UPPER("first_name" || ' ' || "last_name" )));'''
            ],
            reverse_sql=['DROP INDEX "company_advisor_is_active_upper_name_e0ab1b4f";'],
        ),
    ]
