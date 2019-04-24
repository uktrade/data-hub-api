from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0050_remove_contact_from_model_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='interaction',
                    name='contact',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name='+',
                        to='company.Contact',
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name='interaction',
            name='contact',
        ),
    ]
