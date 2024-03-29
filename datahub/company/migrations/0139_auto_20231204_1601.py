# Generated by Django 3.2.22 on 2023-12-04 16:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0138_export_win_match_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='transfer_reason',
            field=models.CharField(blank=True, choices=[('duplicate', 'Duplicate record')], help_text='The reason data for this company was transferred.', max_length=255),
        ),
        migrations.AddField(
            model_name='contact',
            name='transferred_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contact',
            name='transferred_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='transferred_to',
            field=models.ForeignKey(blank=True, help_text='Where data about this company was transferred to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferred_from', to='company.contact'),
        ),
    ]
