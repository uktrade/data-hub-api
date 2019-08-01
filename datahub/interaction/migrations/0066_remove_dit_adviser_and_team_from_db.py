from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0065_remove_dit_adviser_and_team_from_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='interaction',
                    name='dit_adviser',
                    field=models.ForeignKey(
                        help_text='This field is deprecated and has been replaced by DIT '
                                  'participants.',
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='interactions',
                        to=settings.AUTH_USER_MODEL
                    ),
                ),
                migrations.AddField(
                    model_name='interaction',
                    name='dit_team',
                    field=models.ForeignKey(
                        help_text='This field is deprecated and has been replaced by DIT '
                                  'participants.',
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='metadata.Team'
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name='interaction',
            name='dit_adviser',
        ),
        migrations.RemoveField(
            model_name='interaction',
            name='dit_team',
        ),
    ]
