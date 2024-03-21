from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def add_2022_gva_multipliers(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / '0017_add_2022_gva_multipliers.yaml'
    )

def reverse_add_2022_gva_multipliers(apps, schema_editor):
    GVAMultiplier = apps.get_model('investment', 'GVAMultiplier')
    GVAMultiplier.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0016_alter_gvamultiplier_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(
            add_2022_gva_multipliers,
            reverse_add_2022_gva_multipliers,
        ),
    ]
