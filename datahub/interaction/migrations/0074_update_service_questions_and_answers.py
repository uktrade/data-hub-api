from pathlib import PurePath
from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def load_service_questions_and_answers(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0074_update_service_questions_and_answers.yaml',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('metadata', '0008_update_services'),
        ('interaction', '0073_add_trade_agreement_to_interaction_theme'),
    ]

    operations = [
        migrations.RunPython(
            code=load_service_questions_and_answers,
            reverse_code=migrations.RunPython.noop,
        ),
    ]



