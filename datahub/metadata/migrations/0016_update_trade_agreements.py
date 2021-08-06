from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_trade_agreements(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0016_update_trade_agreements.yaml'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0015_remove_puerto_rico'),
    ]

    operations = [
        migrations.RunPython(load_trade_agreements, migrations.RunPython.noop),
    ]
