# Generated by Django 3.2.22 on 2023-10-13 10:31

from django.db import migrations, models
from pathlib import PurePath
import uuid

from datahub.core.migration_utils import load_yaml_data_in_migration

def load_team_types(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0001_initial.yaml'
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TeamType',
            fields=[
                ('disabled_on', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField(blank=True)),
                ('order', models.FloatField(default=0.0)),
                ('export_win_id', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.RunPython(load_team_types, migrations.RunPython.noop),
    ]