from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_trade_agreements(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0034_update_trade_agreements.yaml'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0033_update_programmes'),
    ]

    operations = [
        migrations.RunPython(load_trade_agreements, migrations.RunPython.noop),
    ]
