from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0031_update_services.yaml',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0030_add_additional_services'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
    ]
