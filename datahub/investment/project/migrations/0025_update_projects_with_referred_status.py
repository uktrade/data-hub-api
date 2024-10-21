from uuid import UUID

from django.db import migrations

from datahub.investment.project.constants import SpecificProgramme as SpecificProgrammeConstantEnum


REFERRED_TO_EYB_PROGRAMME_ID = 'd2593cb3-67e6-4fdd-9168-0495752ca483'
REFERRED_STATUS_VALUE = 'referred'
ONGOING_STATUS_VALUE = 'ongoing'


def update_referred_projects_programme_and_status(apps, schema_editor):
    SpecificProgrammeModel = apps.get_model('investment', 'SpecificProgramme')
    referred_to_eyb_programme = SpecificProgrammeModel.objects.get(
        pk=UUID(REFERRED_TO_EYB_PROGRAMME_ID)
    )
    
    InvestmentProjectModel = apps.get_model('investment', 'InvestmentProject')
    referred_projects = InvestmentProjectModel.objects.filter(
        status=REFERRED_STATUS_VALUE,
    )
    
    if referred_projects.exists():
        for project in referred_projects:
            # TODO: confirm this is intended action, compared to replacing existing programme
            project.specific_programmes.add(referred_to_eyb_programme)
            project.status = ONGOING_STATUS_VALUE
            # TODO: investigate if we could bulk update to reduce database hits
            project.save()

def reverse_update_referred_projects_programme_and_status(apps, schema_editor):
    SpecificProgrammeModel = apps.get_model('investment', 'SpecificProgramme')
    referred_to_eyb_programme = SpecificProgrammeModel.objects.get(
        pk=UUID(REFERRED_TO_EYB_PROGRAMME_ID)
    )
    
    InvestmentProjectModel = apps.get_model('investment', 'InvestmentProject')
    referred_projects = InvestmentProjectModel.objects.filter(
        status=ONGOING_STATUS_VALUE,
        specific_programmes__name=referred_to_eyb_programme.name,
    )
    
    if referred_projects.exists():
        for project in referred_projects:
            # TODO: update depending on decided action
            project.specific_programmes.remove(referred_to_eyb_programme)
            project.status = REFERRED_STATUS_VALUE
            # TODO: same as above, investigate efficiency improvements
            project.save()


class Migration(migrations.Migration):
    dependencies = [
        ('investment', '0024_add_referred_to_eyb_specific_programme'),
    ]

    operations = [
        migrations.RunPython(
            code=update_referred_projects_programme_and_status,
            reverse_code=reverse_update_referred_projects_programme_and_status,   
        ),
    ]
