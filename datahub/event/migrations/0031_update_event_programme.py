from pathlib import PurePath
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def update_event_programmes(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / "0031_update_event_programme.yaml"
    )


class Migration(migrations.Migration):
    dependencies = [
        ('event', '0030_add_stova_event_relation'),
    ]

    operations = [
        migrations.RunPython(update_event_programmes, migrations.RunPython.noop),
    ]
