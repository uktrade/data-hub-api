# Generated by Django 4.2.20 on 2025-03-26 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_activity', '0034_set_null_when_related_object_deleted'),
    ]

    operations = [
        migrations.CreateModel(
            name='TempRelationStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_name', models.CharField(max_length=255)),
                ('object_id', models.CharField(max_length=255)),
            ],
        ),
    ]
