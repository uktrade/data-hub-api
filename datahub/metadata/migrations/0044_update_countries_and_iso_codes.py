from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_countries(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0044_update_countries_and_iso_codes.yaml'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0043_update_services'),
    ]

    operations = [
        migrations.RunPython(load_countries, migrations.RunPython.noop),
    ]
