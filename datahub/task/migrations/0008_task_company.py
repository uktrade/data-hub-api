# Generated by Django 3.2.23 on 2023-11-30 15:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0138_export_win_match_id'),
        ('task', '0007_delete_investmentprojecttask'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='task_company', to='company.company'),
        ),
    ]