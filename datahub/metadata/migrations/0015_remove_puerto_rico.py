from django.db import migrations, models
from datahub.metadata.models import AdministrativeArea, Country

def delete_puerto_rico(apps, scheme_editor):
    try:
        puerto_rico = AdministrativeArea.objects.get(pk='4a6f5211-9e54-42e9-ba25-7c67be785d1a')
        puerto_rico.delete()
    except AdministrativeArea.DoesNotExist:
        pass

def restore_puerto_rico(apps, scheme_editor):
    AdministrativeArea.objects.create(pk='4a6f5211-9e54-42e9-ba25-7c67be785d1a',
        name='Puerto Rico',
        area_code='PR',
        country=Country.objects.get(pk='81756b9a-5d95-e211-a939-e4115bead28a')
    )

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0014_update_services'),
    ]

    operations = [
        migrations.RunPython(delete_puerto_rico, restore_puerto_rico)
    ]
