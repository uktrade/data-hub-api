# Generated by Django 3.0.5 on 2020-04-30 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_list', '0013_auto_20200423_1634'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='pipelineitem',
            name='unique_adviser_and_company',
        ),
        migrations.AddField(
            model_name='pipelineitem',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
