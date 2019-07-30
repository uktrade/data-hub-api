from django.db import migrations, models


class Migration(migrations.Migration):
    # This is needed so that we can use CREATE INDEX CONCURRENTLY
    atomic = False

    dependencies = [
        ('interaction', '0062_disable_making_introductions_serviceansweroptions'),
    ]

    operations = [
        # Note that we are using SeparateDatabaseAndState only so that we can use
        # CREATE INDEX CONCURRENTLY.
        # After squashing, migrations.SeparateDatabaseAndState should be removed and
        # just migrations.AddIndex used instead.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name='interaction',
                    index=models.Index(fields=['company', '-date', '-created_on', 'id'],
                                       name='interaction_company_236ca9_idx'),
                ),
            ],
            database_operations=[
                migrations.RunSQL("""
CREATE INDEX CONCURRENTLY "interaction_company_236ca9_idx"
ON "interaction_interaction" ("company_id", "date"DESC, "created_on"DESC, "id");
"""
                )
            ],
        ),
    ]
