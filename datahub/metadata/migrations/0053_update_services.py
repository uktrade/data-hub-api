from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0053_update_services.yaml'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('interaction', '0081_auto_20230130_1124'),
        ('metadata', '0052_update_services'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
    ]
