from pathlib import PurePath
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def update_event_types(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / "0022_update_event_types.yaml"
    )


class Migration(migrations.Migration):
    dependencies = [
        ('event', '0021_update_event_types'),
    ]

    operations = [
        migrations.RunPython(update_event_types, migrations.RunPython.noop),
    ]
