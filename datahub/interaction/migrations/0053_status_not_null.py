from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0052_add_theme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interaction',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('complete', 'Complete')], default='complete', max_length=255),
        ),
    ]
