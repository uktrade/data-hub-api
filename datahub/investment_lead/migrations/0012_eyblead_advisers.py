# Generated by Django 4.2.20 on 2025-04-07 14:17

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('investment_lead', '0011_alter_eyblead_intent_alter_eyblead_landing_timeframe_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='eyblead',
            name='advisers',
            field=models.ManyToManyField(related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
