from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0054_location_not_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interaction',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
