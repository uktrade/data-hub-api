# Generated by Django 3.2.20 on 2023-11-14 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0068_update_sectors'),
    ]

    operations = [
        migrations.AddField(
            model_name='sector',
            name='export_win_id',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
