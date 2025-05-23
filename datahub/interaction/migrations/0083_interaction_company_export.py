# Generated by Django 4.2.16 on 2024-12-09 15:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0144_update_company_export_experience'),
        ('interaction', '0082_alter_interaction_company_alter_interaction_contacts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='interaction',
            name='company_export',
            field=models.ForeignKey(blank=True, help_text='For Export theme only.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='company.companyexport'),
        ),
    ]
