from pathlib import PurePath

import mptt
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, _):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0095_update_service.yaml'
    )


def rebuild_tree(apps, _):
    Service = apps.get_model('metadata', 'Service')
    manager = mptt.managers.TreeManager()
    manager.model = Service
    mptt.register(Service, order_insertion_by=['segment'])
    manager.contribute_to_class(Service, 'objects')
    manager.rebuild()


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0094_update_investment_business_activities'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
        migrations.RunPython(rebuild_tree, migrations.RunPython.noop),
    ]
