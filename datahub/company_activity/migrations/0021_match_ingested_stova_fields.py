# Generated by Django 4.2.16 on 2024-12-10 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_activity', '0020_rename_event_id_from_stova'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stovaevent',
            name='client_contact',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stovaevent',
            name='created_by',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='stovaevent',
            name='modified_by',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
