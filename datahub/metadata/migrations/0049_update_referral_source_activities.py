from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_referral_source_activities(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0049_update_referral_source_activities.yaml'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0048_update_services'),
    ]

    operations = [
        migrations.RunPython(load_referral_source_activities, migrations.RunPython.noop),
    ]
