from django.db import migrations

from datahub.core.migration_utils import DeleteModelWithMetadata


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0098_company_dnb_modified_on'),
    ]

    operations = [
        DeleteModelWithMetadata(
            name='companieshousecompany',
        ),
    ]
