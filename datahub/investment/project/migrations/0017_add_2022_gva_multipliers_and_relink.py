from pathlib import PurePath

from django.db import migrations
from django.db.models import Q

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.core.migration_utils import load_yaml_data_in_migration
from datahub.investment.project.gva_utils import set_gross_value_added_for_investment_project


def add_2022_gva_multipliers(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / '0017_add_2022_gva_multipliers_and_relink.yaml'
    )

def reverse_add_2022_gva_multipliers(apps, schema_editor):
    GVAMultiplier = apps.get_model('investment', 'GVAMultiplier')
    GVAMultiplier.objects.all().delete()

def relink_investment_projects_with_gva_multipliers(apps, schema_editor):
    InvestmentProject = apps.get_model('investment', 'InvestmentProject')
    queryset = InvestmentProject.objects.filter(
        investment_type_id=InvestmentTypeConstant.fdi.value.id,
    ).filter(
        Q(
            sector__isnull=False,
        ) | Q(
            business_activities__in=[
                InvestmentBusinessActivityConstant.retail.value.id,
                InvestmentBusinessActivityConstant.sales.value.id,
            ],
        ),
    )
    for project in queryset:
        set_gross_value_added_for_investment_project(project)
        project.save()

def reverse_relink_investment_projects_with_gva_multipliers(apps, schema_editor):
    InvestmentProject = apps.get_model('investment', 'InvestmentProject')
    queryset = InvestmentProject.objects.all()
    queryset.update(
        gva_multiplier=None,
        gross_value_added=None,
    )

class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0016_alter_gvamultiplier_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(
            add_2022_gva_multipliers,
            reverse_add_2022_gva_multipliers,
        ),
        migrations.RunPython(
            relink_investment_projects_with_gva_multipliers,
            reverse_relink_investment_projects_with_gva_multipliers,
        ),
    ]
