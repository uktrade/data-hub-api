from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investment_lead', '0007_alter_eyblead_hiring_alter_eyblead_spend'),
    ]

    operations = [
        migrations.AddField(
            model_name='eyblead',
            name='marketing_hashed_uuid',
            field=models.CharField(blank=True, max_length=256),
        ),
    ]
