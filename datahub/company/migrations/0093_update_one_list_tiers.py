from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_one_list_tiers(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0093_one_list_tiers.yaml',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0092_company_export_potential'),
    ]

    operations = [
        migrations.RunPython(load_one_list_tiers, migrations.RunPython.noop)
    ]
