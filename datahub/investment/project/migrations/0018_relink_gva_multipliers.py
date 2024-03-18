from django.db import migrations
from django.db.models import Q

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.investment.project.gva_utils import set_gross_value_added_for_investment_project


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


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0017_add_2022_gva_multipliers')
    ]

    operations = [
        migrations.RunPython(
            relink_investment_projects_with_gva_multipliers,
            migrations.RunPython.noop,
        ),
    ]
