from django.db import migrations


CAPITAL_ONLY_FDI_TYPE_PK = '840f62c1-bbcb-44e4-b6d4-a258d2ffa07d'


def change_fdi_type_name(apps, schema_editor):
    FDIType = apps.get_model('metadata', 'FDIType')   
    try:
        capital_only_fdi_type= FDIType.objects.get(pk=CAPITAL_ONLY_FDI_TYPE_PK)
        capital_only_fdi_type.name = 'Capital only (minimum investment value is £15 million)'
        capital_only_fdi_type.save()
    except FDIType.DoesNotExist:
        pass


def reverse_change_fdi_type_name(apps, schema_editor):
    FDIType = apps.get_model('metadata', 'FDIType')
    try:
        capital_only_fdi_type = FDIType.objects.get(pk=CAPITAL_ONLY_FDI_TYPE_PK)
        capital_only_fdi_type.name = 'Capital only'
        capital_only_fdi_type.save()
    except FDIType.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0082_add_eyb_referral_source_activity'),
    ]

    operations = [
        migrations.RunPython(change_fdi_type_name, reverse_change_fdi_type_name),
    ]
