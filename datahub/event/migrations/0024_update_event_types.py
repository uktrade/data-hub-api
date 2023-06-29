from django.utils.timezone import now
from pathlib import PurePath
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def update_event_types(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / "0024_update_event_types.yaml"
    )


def disable_event_type(apps, schema_editor):
    EventType = apps.get_model('event', 'EventType')
    try:
        # Disable Event Type { name: "Export Academy", pk: "543e4ca4-ed74-d60f-f6bf-1a0fd64b772d" }
        event_type = EventType.objects.get(pk='543e4ca4-ed74-d60f-f6bf-1a0fd64b772d')
        event_type.disabled_on = now()
        event_type.save()
    except EventType.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('event', '0023_update_event_programme'),
    ]

    operations = [
        migrations.RunPython(update_event_types, migrations.RunPython.noop),
        migrations.RunPython(disable_event_type, migrations.RunPython.noop),
    ]
