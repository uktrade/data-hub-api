# Generated by Django 3.2.19 on 2023-07-31 12:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('event', '0025_update_event_types'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailboxLogging',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('retrieved_on', models.DateTimeField()),
                ('source', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('retrieved', 'Retrieved'), ('processed', 'Processed'), ('failure', 'Failure'), ('unknown', 'Unknown')], default='unknown', max_length=255)),
                ('extra', models.TextField(blank=True)),
                ('interaction', models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='mailbox', to='interaction.interaction')),
            ],
        ),
    ]
