from django.db import migrations, models

def delete_puerto_rico(apps, scheme_editor):
    model = apps.get_model('metadata.administrativearea')
    model.objects.get(pk='4a6f5211-9e54-42e9-ba25-7c67be785d1a').delete()

def readd_puerto_rico(apps, scheme_editor):
    model = apps.get_model('metadata.administrativearea')
    model.object.create(pk='4a6f5211-9e54-42e9-ba25-7c67be785d1a',
        name='Puerto Rico',
        area_code='PR',
        country='81756b9a-5d95-e211-a939-e4115bead28a'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('company', '0111_add_telephone_validation'),
    ]

    operations = [
        migrations.RunPython(delete_puerto_rico),
        migrations.RunPython(delete_puerto_rico, readd_puerto_rico)
    ]
