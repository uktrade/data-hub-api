# Generated by Django 4.2.17 on 2025-02-25 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_activity', '0032_make_event_not_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stovaevent',
            name='contact_info',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
