from django.db import migrations

from datahub.investment.project.gva_utils import set_gross_value_added_for_investment_project
from datahub.investment.project.tasks import get_investment_projects_to_refresh_gva_values



def relink_investment_projects_with_gva_multipliers(apps, schema_editor):
    projects = get_investment_projects_to_refresh_gva_values()
    for project in projects.iterator():
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
