# Generated by Django 4.2.17 on 2025-02-14 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_activity', '0026_allow_bank_values_for_event_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stovaevent',
            name='code',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='stovaevent',
            name='timezone',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]
