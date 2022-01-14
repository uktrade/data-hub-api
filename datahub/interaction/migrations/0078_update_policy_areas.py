from django.db import migrations
from datahub.core.migration_utils import load_yaml_data_in_migration
from pathlib import PurePath

def load_new_trade_agreements(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0078_update_policy_areas.yaml',
    )

class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0077_add_new_policy_areas'),
    ]

    operations = [
        migrations.RunPython(
            code=load_new_trade_agreements,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
