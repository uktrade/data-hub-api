from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def update_specific_programmes(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / "0005_update_specific_programmes.yaml"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0004_auto_20210922_1706"),
    ]

    operations = [
        migrations.RunPython(update_specific_programmes, migrations.RunPython.noop),
    ]
