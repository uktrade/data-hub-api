# Generated by Django 3.2.20 on 2023-09-18 15:44

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reminder', '0008_create_reminder_for_new_export_interactions'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpcomingTaskReminderSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('reminder_days', django.contrib.postgres.fields.ArrayField(base_field=models.PositiveSmallIntegerField(), blank=True, default=list, size=5)),
                ('email_reminders_enabled', models.BooleanField(default=False)),
                ('adviser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]