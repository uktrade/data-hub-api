# Generated by Django 4.2.15 on 2024-09-25 10:15

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("company_activity", "0002_companyactivity_investment"),
    ]

    operations = [
        migrations.CreateModel(
            name="IngestedFile",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                (
                    "filepath",
                    models.CharField(
                        help_text="The S3 object path including prefix of the ingested file",
                        max_length=255,
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]