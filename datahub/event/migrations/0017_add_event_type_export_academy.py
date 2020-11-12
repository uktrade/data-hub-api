from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_add_event(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parents[1] / 'fixtures/add_event_type_export_academy.yaml',
    )

class Migration(migrations.Migration):

    dependencies = [
        ('event', '0016_add_composite_index_to_event'),
    ]

    operations = [
        migrations.RunPython(load_add_event, migrations.RunPython.noop),
    ]
