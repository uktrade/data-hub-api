from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0030_update_permissions_django_21'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='company',
                    name='parent',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='+',
                        to='company.Company'
                    )
                ),
            ],
        ),
        migrations.RemoveField(
            model_name='company',
            name='parent',
        ),
    ]
