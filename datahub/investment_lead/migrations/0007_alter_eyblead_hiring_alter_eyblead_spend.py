# Generated by Django 4.2.16 on 2024-10-23 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investment_lead', '0006_rename_location_city_eyblead_proposed_investment_city_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eyblead',
            name='hiring',
            field=models.CharField(blank=True, choices=[('1-10', '1 to 10'), ('11-50', '11 to 50'), ('1-5', '1 to 5'), ('6-50', '6 to 50'), ('51-100', '51 to 100'), ('101+', 'More than 100'), ('NO_PLANS_TO_HIRE_YET', 'No plans to hire')], default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='eyblead',
            name='spend',
            field=models.CharField(blank=True, choices=[('500001-1000000', '£500,001 - £1,000,000'), ('1000001-2000000', '£1,000,001 - £2,000,000'), ('2000001-5000000', '£2,000,001 - £5,000,000'), ('5000001-10000000', '£5,000,001 - £10,000,000'), ('10000001+', 'More than £10 million'), ('SPECIFIC_AMOUNT', 'Specific amount'), ('0-9999', 'Less than £10,000'), ('10000-500000', '£10,000 to £500,000'), ('500000-1000000', '£500,000 to £1 million'), ('1000000-2000000', '£1 million to £2 million'), ('2000000-5000000', '£2 million to £5 million'), ('5000000-10000000', '£5 million to £10 million'), ('10000000+', 'More than £10 million')], default='', max_length=256),
        ),
    ]