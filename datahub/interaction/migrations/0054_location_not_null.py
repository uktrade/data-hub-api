from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0053_status_not_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interaction',
            name='location',
            field=models.CharField(default='', max_length=255),
        ),
    ]
