from uuid import UUID

from django.db import migrations, transaction


REFERRED_TO_EYB_PROGRAMME_ID = UUID('3902b516-e553-4f54-b389-0a5db87ea507')
REFERRED_STATUS_VALUE = 'referred'
ONGOING_STATUS_VALUE = 'ongoing'


def update_referred_projects_programme_and_status(apps, schema_editor):    
    InvestmentProjectModel = apps.get_model('investment', 'InvestmentProject')
    referred_projects = InvestmentProjectModel.objects.filter(
        status=REFERRED_STATUS_VALUE,
    )
    SpecificProgrammeModel = apps.get_model('investment', 'SpecificProgramme')
    referred_to_eyb_programme = SpecificProgrammeModel.objects.get(
        pk=REFERRED_TO_EYB_PROGRAMME_ID
    )
    if referred_projects.exists():
            # many-to-many field needs to be updated individually
            for project in referred_projects:
                project.specific_programmes.add(referred_to_eyb_programme)
            # bulk update status field
            referred_projects.update(status=ONGOING_STATUS_VALUE)


class Migration(migrations.Migration):
    dependencies = [
        ('investment', '0024_add_referred_to_eyb_specific_programme'),
    ]

    operations = [
        migrations.RunPython(
            code=update_referred_projects_programme_and_status,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
