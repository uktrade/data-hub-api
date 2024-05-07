from django.db import migrations
from pathlib import PurePath
import uuid

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_team_types(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0040_add_team.yaml'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0039_win_adviser_email_address_win_adviser_name_and_more'), # .py
    ]

    operations = [
        migrations.RunPython(load_team_types, migrations.RunPython.noop),
    ]
