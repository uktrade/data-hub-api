from django.db import migrations, models
from pathlib import PurePath
import uuid


from datahub.core.migration_utils import load_yaml_data_in_migration


def load_associated_programmes(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0047_add_associated_programmes.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0046_fix_hq_team_migration'),
    ]

    operations = [
        migrations.RunPython(load_associated_programmes, migrations.RunPython.noop),
    ]
