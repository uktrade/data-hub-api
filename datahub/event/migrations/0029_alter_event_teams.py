# Generated by Django 4.2.15 on 2024-09-25 10:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0087_update_services'),
        ('event', '0028_update_event_programme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='teams',
            field=models.ManyToManyField(blank=True, related_name='+', to='metadata.team'),
        ),
    ]
