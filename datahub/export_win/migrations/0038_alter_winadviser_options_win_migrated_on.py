# Generated by Django 4.2.10 on 2024-04-17 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0037_alter_win_sector'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='winadviser',
            options={'verbose_name': 'Adviser'},
        ),
        migrations.AddField(
            model_name='win',
            name='migrated_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]