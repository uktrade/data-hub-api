from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_countries(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0046_update_countries.yaml'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0045_alter_country_iso_alpha2_code'),
    ]

    operations = [
        migrations.RunPython(load_countries, migrations.RunPython.noop),
    ]
