from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_support', '0004_add_country_to_simple_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='simplemodel',
            name='address',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
