# Generated by Django 3.2.23 on 2024-01-12 15:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reminder', '0021_taskcompletedreminder_taskcompletedsubscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskDeletedByOthersSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('email_reminders_enabled', models.BooleanField(default=False)),
                ('adviser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]