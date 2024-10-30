from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def add_eyb_specific_programme(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / '0024_add_referred_to_eyb_specific_programme.yaml'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('investment', '0023_remove_investmentproject_specific_programme_and_more'),
    ]

    operations = [
        migrations.RunPython(
            code=add_eyb_specific_programme,
            # for reverse_code, do nothing to avoid handling future projects with this status
            reverse_code=migrations.RunPython.noop,
        ),
    ]
