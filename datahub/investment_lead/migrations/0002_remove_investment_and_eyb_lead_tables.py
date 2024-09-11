"""Migration to remove initial InvestmentLead and EYBLead tables.

This is needed because a new primary key field is added in investment_lead migration 0003.
Rather than go down the route suggested by the documentation (see 
https://docs.djangoproject.com/en/4.2/howto/writing-migrations/#migrations-that-add-unique-fields),
it was decided it would be easier to remove the tables and start fresh because
there is no lead data in any environment at the time of creating this migration.
"""

from django.db import migrations


def assert_no_leads(apps, schema_editor):
    InvestmentLead = apps.get_model('investment_lead', 'InvestmentLead')
    EYBLead = apps.get_model('investment_lead', 'EYBLead')
    assert not InvestmentLead.objects.exists()
    assert not EYBLead.objects.exists()


class Migration(migrations.Migration):

    dependencies = [
        ('investment_lead', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            assert_no_leads,
            reverse_code=migrations.RunPython.noop,    
        ),
        migrations.DeleteModel(
            name='InvestmentLead',
        ),
        migrations.DeleteModel(
            name='EYBLead',
        ),
    ]
