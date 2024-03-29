# Generated by Django 3.2.13 on 2022-05-23 12:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('investment', '0005_update_specific_programmes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reminder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpcomingEstimatedLandDateReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('event', models.CharField(max_length=255)),
                ('adviser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upcoming_estimated_land_date_reminders', to='investment.investmentproject')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NoRecentInvestmentInteractionReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('event', models.CharField(max_length=255)),
                ('adviser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='no_recent_investment_interaction_reminders', to='investment.investmentproject')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
