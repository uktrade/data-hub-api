from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_missing_international_countries(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0010_missing_international_countries.yaml'
    )


def load_administrativearea_codes_associated_with_missing_countries(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0010_new_administrative_areas_linked_with_missing_countries.yaml'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0009_existing_international_administrativearea_area_code'),
    ]

    operations = [
        migrations.RunPython(load_missing_international_countries, migrations.RunPython.noop),
        migrations.RunPython(load_administrativearea_codes_associated_with_missing_countries,
                             migrations.RunPython.noop),
    ]
