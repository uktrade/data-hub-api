from django.db import migrations
from django.db.models import Q
from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.investment.project.gva_utils import set_gross_value_added_for_investment_project


BATCH_SIZE = 500

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
    ).only(
        'id',
        'foreign_equity_investment',
        'number_new_jobs',
        'sector',
        'business_activities',
    )
    while True:
        batch = list(queryset[:BATCH_SIZE])
        if not batch:
            break
        updates = []
        for project in batch:
            gva_data = set_gross_value_added_for_investment_project(project)
            updates.append(
                InvestmentProject(
                    id=project.id,
                    gva_multiplier=gva_data.gva_multiplier, 
                    gross_value_added=gva_data.gross_value_added
                )
            )
        InvestmentProject.objects.bulk_update(updates, ['gva_multiplier', 'gross_value_added'])
        queryset = queryset[BATCH_SIZE:]

def reverse_relink_investment_projects_with_gva_multipliers(apps, schema_editor):
    InvestmentProject = apps.get_model('investment', 'InvestmentProject')
    queryset = InvestmentProject.objects.all()
    queryset.update(
        gva_multiplier=None,
        gross_value_added=None,
    )

class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0017_add_2022_gva_multipliers_and_relink'),
    ]

    operations = [
        migrations.RunPython(
            relink_investment_projects_with_gva_multipliers,
            reverse_relink_investment_projects_with_gva_multipliers,
        ),
    ]
