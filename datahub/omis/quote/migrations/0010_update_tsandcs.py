from __future__ import unicode_literals
from pathlib import PurePath

from django.core.management import call_command
from django.db import migrations
from datahub.core.migration_utils import load_yaml_data_in_migration


def load_updated_ts_and_cs(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parents[1] / 'fixtures/terms_and_conditions_v1_1.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('omis_quote', '0009_auto_20210816_1601'),
    ]

    operations = [
        migrations.RunPython(load_updated_ts_and_cs, migrations.RunPython.noop),
    ]
