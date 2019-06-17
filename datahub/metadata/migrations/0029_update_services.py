from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_administrative_areas(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0029_update_services.yaml',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0028_add_requires_service_answers_flow_feature_flag'),
    ]

    operations = [
        migrations.RunPython(load_administrative_areas, migrations.RunPython.noop),
    ]
