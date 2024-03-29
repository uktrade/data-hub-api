# Generated by Django 3.2.22 on 2023-10-23 11:05

from django.db import migrations, models
from pathlib import PurePath
import uuid

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_support_types(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0005_add_support_type.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0004_add_business_potential'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportType',
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
        migrations.RunPython(load_support_types, migrations.RunPython.noop),
    ]
