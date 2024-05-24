from django.db import migrations
from pathlib import PurePath

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_team_types(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0046_fix_hq_team_migration.yaml'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0045_alter_breakdown_year'),
    ]

    operations = [
        migrations.RunPython(load_team_types, migrations.RunPython.noop),
    ]
