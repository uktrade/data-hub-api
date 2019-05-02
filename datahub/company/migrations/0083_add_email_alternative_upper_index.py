"""
Creates an index on UPPER(email_alternative) on the Contact model (for use with the
iexact filter look-up).

As Django does not support creating indexes on expressions, SQL is used.

The migration is run inside a transaction, so CREATE INDEX CONCURRENTLY is not used.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0082_make_registered_address_country_optional'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                '''CREATE INDEX "company_contact_upper_email_alternative_eb17a977"
ON "company_contact" (UPPER("email_alternative"));'''
            ],
            reverse_sql=['DROP INDEX "company_contact_upper_email_alternative_eb17a977";'],
        ),
    ]
