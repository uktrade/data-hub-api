from pathlib import PurePath

from django.db import migrations, models
import uuid

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_initial_inner_template(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0002_notificationinnertemplate.yaml',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationInnerTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('notification_type', models.CharField(choices=[('not_set', 'Not set'), ('no_investment_recent_interaction', 'No investment recent interaction'), ('upcoming_estimated_land_date', 'Upcoming estimated land date')], default='not_set', max_length=255, unique=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RunPython(load_initial_inner_template, migrations.RunPython.noop),
    ]
