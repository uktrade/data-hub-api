from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_disabled_teams(apps, schema_editor):
    load_yaml_data_in_migration(
        # Update to reflect yaml filename.
        apps, PurePath(__file__).parent / "0053_disable_teams.yaml"
    )


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0052_add_team'),
    ]

    operations = [
        migrations.RunPython(load_disabled_teams, migrations.RunPython.noop),
    ]
