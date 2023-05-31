from django.db import migrations, models
from datahub.core.migration_utils import load_yaml_data_in_migration
from pathlib import PurePath

def load_new_statuses(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0080_add_new_statuses.yaml',
    )

class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0079_add_new_policy_areas'),
    ]

    operations = [
        migrations.RunPython(
            code=load_new_statuses,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
