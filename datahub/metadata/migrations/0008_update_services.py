from pathlib import PurePath

import mptt
from django.db import migrations

import datahub
from datahub.core.migration_utils import load_yaml_data_in_migration


def load_services(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0008_update_services.yaml'
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
        ('metadata', '0007_administrativearea_area_code'),
    ]

    operations = [
        migrations.AlterField(
                            model_name='service',
                            name='contexts',
                            field=datahub.core.fields.MultipleChoiceField(blank=True, choices=(('event', 'Event'), ('export_interaction', 'Export interaction'), ('export_service_delivery', 'Export service delivery'), ('investment_interaction', 'Investment interaction'), ('investment_project_interaction', 'Investment project interaction'), ('trade_agreement_interaction', 'Trade agreement interaction'), ('other_interaction', 'Other interaction'), ('other_service_delivery', 'Other service delivery'), ('interaction', 'Interaction (deprecated)'), ('service_delivery', 'Service delivery (deprecated)')), help_text='Contexts are only valid on leaf nodes.', max_length=255),
                        ),
        migrations.RunPython(load_services, migrations.RunPython.noop),
        migrations.RunPython(rebuild_tree, migrations.RunPython.noop),
    ]
