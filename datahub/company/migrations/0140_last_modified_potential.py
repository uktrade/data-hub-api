from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0139_auto_20231204_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='last_modified_potential',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp of the last modification for export potential.'),
        ),
    ]
