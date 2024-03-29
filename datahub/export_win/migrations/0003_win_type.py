# Generated by Django 3.2.22 on 2023-10-13 10:31

from django.db import migrations, models
from pathlib import PurePath
import uuid

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_win_types(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0003_win_type.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0002_add_hq_team_region_or_post'),
    ]

    operations = [
        migrations.CreateModel(
            name='WinType',
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
        migrations.RunPython(load_win_types, migrations.RunPython.noop),
    ]
