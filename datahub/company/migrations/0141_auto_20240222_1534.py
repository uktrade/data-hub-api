# Generated by Django 3.2.24 on 2024-02-22 15:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0140_last_modified_potential'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='transfer_reason',
            field=models.CharField(blank=True, choices=[('duplicate', 'Duplicate record')], help_text='The reason data for this contact was transferred.', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='transferred_to',
            field=models.ForeignKey(blank=True, help_text='Where data about this contact was transferred to.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferred_from', to='company.contact'),
        ),
    ]