# Generated by Django 3.2.21 on 2023-11-07 07:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('task', '0005_task_reminder_date'),
        ('reminder', '0016_merge_20231102_1139'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskAmendedByOthersSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('email_reminders_enabled', models.BooleanField(default=False)),
                ('adviser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaskAmendedByOthersReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('event', models.CharField(max_length=255)),
                ('status', models.CharField(blank=True, choices=[('live', 'Live'), ('dismissed', 'Dismissed')], default='live', max_length=255)),
                ('email_notification_id', models.UUIDField(blank=True, null=True)),
                ('email_delivery_status', models.CharField(blank=True, choices=[('sending', 'Sending'), ('delivered', 'Delivered'), ('permanent-failure', 'Permanent failure'), ('temporary-failure', 'Temporary failure'), ('technical-failure', 'Technical failure'), ('unknown', 'Unknown')], default='unknown', help_text='Email delivery status', max_length=255)),
                ('adviser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_amended_by_others_reminder', to='task.task')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
