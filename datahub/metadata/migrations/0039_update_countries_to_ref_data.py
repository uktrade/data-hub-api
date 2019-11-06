from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_countries(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0039_rename_countries.yaml',
    )

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0038_remove_service_name_from_db'),
    ]

    operations = [
        migrations.RunPython(load_countries, migrations.RunPython.noop),
    ]
