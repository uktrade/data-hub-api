from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('search_support', '0005_add_address_to_simple_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='simplemodel',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
