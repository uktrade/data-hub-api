from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0035_remove_requires_service_answers_flow_feature_flag_from_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='service',
                    name='requires_service_answers_flow_feature_flag',
                    field=models.BooleanField(default=False, null=True),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name='service',
            name='requires_service_answers_flow_feature_flag',
        )
    ]
