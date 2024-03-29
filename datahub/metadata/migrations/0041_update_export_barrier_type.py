# Generated by Django 3.2.16 on 2023-01-26 10:03

from django.db import migrations
from pathlib import PurePath

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_services(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0041_update_export_barrier_type.yaml'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0040_update_trade_agreements'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
    ]
