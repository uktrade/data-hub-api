from pathlib import PurePath
from uuid import UUID

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration
from datahub.investment.project.constants import SpecificProgramme as SpecificProgrammeConstantEnum


REFERRED_TO_EYB_PROGRAMME_ID = 'd2593cb3-67e6-4fdd-9168-0495752ca483'


def add_eyb_specific_programmes(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / '0024_add_referred_to_eyb_specific_programme.yaml'
    )

def reverse_add_eyb_specific_programmes(apps, schema_editor):
    SpecificProgrammeModel = apps.get_model('investment', 'SpecificProgramme')
    SpecificProgrammeModel.objects.filter(
        pk=UUID(REFERRED_TO_EYB_PROGRAMME_ID)
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('investment', '0023_remove_investmentproject_specific_programme_and_more'),
    ]

    operations = [
        migrations.RunPython(
            code=add_eyb_specific_programmes,
            reverse_code=reverse_add_eyb_specific_programmes,
        ),
    ]
