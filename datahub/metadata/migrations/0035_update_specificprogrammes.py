from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def update_specific_programmes(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / "0035_update_specificprogrammes.yaml"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("metadata", "0034_update_trade_agreements"),
    ]

    operations = [
        migrations.RunPython(update_specific_programmes, migrations.RunPython.noop),
    ]
