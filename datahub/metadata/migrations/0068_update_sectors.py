from pathlib import PurePath

import mptt
from django.conf import settings
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, _):
    if settings.SECTOR_ENVIRONMENT == 'production':
        return

    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0068_update_sectors.yaml'
    )


def rebuild_tree(apps, _):
    if settings.SECTOR_ENVIRONMENT == 'production':
        return

    Service = apps.get_model('metadata', 'Sector')
    manager = mptt.managers.TreeManager()
    manager.model = Service
    mptt.register(Service, order_insertion_by=['segment'])
    manager.contribute_to_class(Service, 'objects')
    manager.rebuild()


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0067_update_services'),
    ]

    operations = [
        migrations.RunPython(load_services, migrations.RunPython.noop),
        migrations.RunPython(rebuild_tree, migrations.RunPython.noop),
    ]
