from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('interaction', '0062_disable_making_introductions_serviceansweroptions'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='interaction',
            index=models.Index(fields=['company', '-date', '-created_on', 'id'],
                               name='interaction_company_236ca9_idx'),
        ),
    ]
