# Generated by Django 3.2.18 on 2023-05-05 10:12

from django.db import migrations, models

def convert_datetime_to_date(apps, schema_editor):
    CompanyExport = apps.get_model('company', 'CompanyExport')
    for obj in CompanyExport.objects.filter(estimated_win_date__isnull=False):
        obj.estimated_win_date = obj.estimated_win_date.date()
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('company', '0129_alter_companyexport_estimated_win_date'),
    ]

    operations = [
        migrations.RunPython(
            convert_datetime_to_date,
            reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name='companyexport',
            name='estimated_win_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]