from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def update_specific_programmes(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / "0018_update_specific_programmes.yaml"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("investment", "0017_add_2022_gva_multipliers_and_relink"),
    ]

    operations = [
        migrations.RunPython(update_specific_programmes, migrations.RunPython.noop),
    ]
