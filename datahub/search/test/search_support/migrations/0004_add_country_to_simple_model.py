from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search_support', '0003_add_date_to_simple_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='simplemodel',
            name='country',
            field=models.CharField(max_length=50, blank=True),
        ),
    ]
