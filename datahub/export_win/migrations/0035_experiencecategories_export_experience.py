# Generated by Django 4.2.10 on 2024-03-28 14:34

from pathlib import PurePath

from django.db import migrations, models
import django.db.models.deletion

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_migration_data(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0035_experiencecategories_export_experience.yaml'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('company', '0141_auto_20240222_1534'),
        ('export_win', '0034_deletedwin_win_is_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiencecategories',
            name='export_experience',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='export_wins_export_experience', to='company.exportexperience'),
        ),
        migrations.RunPython(load_migration_data, migrations.RunPython.noop),
    ]
