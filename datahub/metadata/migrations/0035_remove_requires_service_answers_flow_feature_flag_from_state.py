from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0034_update_services'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='requires_service_answers_flow_feature_flag',
            field=models.BooleanField(default=False, help_text="Temporary field that designates that this service should be hidden unless the 'interaction_service_answers_flow' feature flag is active.", null=True),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='service',
                    name='requires_service_answers_flow_feature_flag',
                )
            ],
        )
    ]
