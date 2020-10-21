from pathlib import PurePath

import mptt
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0005_update_services.yaml'
    )

def rebuild_tree(apps, schema_editor):
    Service = apps.get_model('metadata', 'Service')
    manager = mptt.managers.TreeManager()
    manager.model = Service
    mptt.register(Service, order_insertion_by=['segment'])
    manager.contribute_to_class(Service, 'objects')
    manager.rebuild()


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0004_update_services'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
        migrations.RunPython(rebuild_tree, migrations.RunPython.noop),
    ]
    