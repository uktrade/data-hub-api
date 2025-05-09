from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_investment_business_activities(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0094_update_investment_business_activities.yaml'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0093_update_services'),
    ]

    operations = [
        migrations.RunPython(load_investment_business_activities, migrations.RunPython.noop),
    ]
