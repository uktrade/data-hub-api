from pathlib import PurePath

from django.core.management import call_command
from django.db import migrations


def unlink_gva_multiplier_from_investment_projects(apps, schema_editor):
    InvestmentProject = apps.get_model('investment', 'InvestmentProject')
    for project in InvestmentProject.objects.all():
        project.gva_multiplier = None
        project.save()


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
