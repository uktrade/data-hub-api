from django.db import migrations

def add_eu_uk_trade_agreement(apps, scheme_editor):
    TradeAgreement = apps.get_model('metadata', 'tradeagreement')
    TradeAgreement.objects.update_or_create(pk='2f796708-ed70-4273-9d92-a671ee567cad',
        name='EU-UK Trade Co-operation Agreement'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0015_remove_puerto_rico'),
    ]

    operations = [
        migrations.RunPython(add_eu_uk_trade_agreement)
    ]
