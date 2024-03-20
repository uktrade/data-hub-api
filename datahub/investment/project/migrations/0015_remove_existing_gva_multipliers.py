from pathlib import PurePath

from django.db import migrations
from django.db.models import Q

from datahub.core.migration_utils import load_yaml_data_in_migration

def unlink_gva_multiplier_from_investment_projects(apps, schema_editor):
    InvestmentProject = apps.get_model('investment', 'InvestmentProject')
    queryset = InvestmentProject.objects.all()
    queryset.update(
        gva_multiplier=None,
        gross_value_added=None,
    )

def clear_gva_multiplier_data(apps, schema_editor):
    GVAMultiplier = apps.get_model('investment', 'GVAMultiplier')
    GVAMultiplier.objects.all().delete()

def reverse_clear_gva_multiplier_data(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / '0001_gvamultiplier.yaml'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0014_update_specific_programmes'),
    ]

    operations = [
        migrations.RunPython(
            unlink_gva_multiplier_from_investment_projects,
            # reliknking projects would raise an error without reverting
            # how GVA is calculated in gva_utils.py
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            clear_gva_multiplier_data,
            # although this reverse function works, you will get an
            # error when attempting to view GVAMultipliers in Django admin;
            # this is due to the lack of GVAMultiplier.sector_id field
            reverse_clear_gva_multiplier_data,
        ),
    ]
