from django.db import migrations, models
from pathlib import PurePath
import uuid


from datahub.core.migration_utils import load_yaml_data_in_migration


def load_associated_programmes(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0039_add_associated_programmes.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0038_alter_winadviser_options_win_migrated_on'),
    ]

    operations = [
        migrations.RunPython(load_associated_programmes, migrations.RunPython.noop),
    ]
