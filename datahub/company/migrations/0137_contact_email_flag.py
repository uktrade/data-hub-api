# Generated by Django 3.2.12 on 2023-09-12 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0136_company_is_out_of_business'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='valid_email',
            field=models.BooleanField(null=True, blank=True),
        ),
    ]
