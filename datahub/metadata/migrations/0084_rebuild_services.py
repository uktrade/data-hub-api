from pathlib import PurePath

import mptt

from django.db import migrations


def rebuild_tree(apps, _):
    Service = apps.get_model('metadata', 'Service')
    manager = mptt.managers.TreeManager()
    manager.model = Service
    mptt.register(Service, order_insertion_by=['segment'])
    manager.contribute_to_class(Service, 'objects')
    manager.rebuild()


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0083_update_services'),
    ]

    operations = [
        migrations.RunPython(rebuild_tree, migrations.RunPython.noop),
    ]
