from django.db import migrations
from django.db.models import Q

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)


def unlink_gva_multiplier_from_investment_projects(apps, schema_editor):
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
    queryset.update(
        gva_multiplier=None,
        gross_value_added=None,
    )

def clear_gva_multiplier_data(apps, schema_editor):
    GVAMultiplier = apps.get_model('investment', 'GVAMultiplier')
    GVAMultiplier.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0014_update_specific_programmes'),
    ]

    operations = [
        migrations.RunPython(
            unlink_gva_multiplier_from_investment_projects,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            clear_gva_multiplier_data,
            migrations.RunPython.noop,
        ),
    ]
