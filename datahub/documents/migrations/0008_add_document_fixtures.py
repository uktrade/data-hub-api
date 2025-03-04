from pathlib import PurePath

from django.db import migrations

from datahub.core.migration_utils import load_yaml_data_in_migration


def add_document_fixtures(apps, schema_editor):
    load_yaml_data_in_migration(
        apps, PurePath(__file__).parent / '0008_add_document_fixtures.yaml'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('documents', '0007_remove_genericdocument_documents_g_documen_7d45ae_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(
            code=add_document_fixtures,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
