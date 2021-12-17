from django.db import migrations, models
from datahub.core.migration_utils import load_yaml_data_in_migration
from pathlib import PurePath

# we'll want to use something like the following, except with the gulf cooperation council being added to the interaction.policyarea
#under: 'Free Trade Agreements: Gulf Cooperation Council'
def load_gulf_cooperation_council(apps, schema_editor):
    load_yaml_data_in_migration(
        apps,
        PurePath(__file__).parent / '0077_add_gulf_cooperation_council.yaml',
    )

class Migration(migrations.Migration):

    dependencies = [
        ('interaction', '0076_interaction_companies'),
    ]

    operations = [
        migrations.RunPython(
            code=load_gulf_cooperation_council,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
