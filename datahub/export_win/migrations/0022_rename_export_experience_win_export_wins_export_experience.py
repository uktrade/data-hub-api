# Generated by Django 3.2.23 on 2024-01-09 11:50

from typing import Any
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
import django.db.models.deletion


class RenameIndexOperation(migrations.RunPython):
    """
    Django currently does not rename the index when corresponding field is renamed,
    so we need to do that manually, so there is no conflict. 
    """

    def __init__(self, model_name, old_field_name, new_field_name):
        self.model_name = model_name
        self.old_field_name = old_field_name
        self.new_field_name = new_field_name
    
    def rename_index(self, schema_editor: BaseDatabaseSchemaEditor, table_name, old_field_name, new_field_name):
        introspection = schema_editor.connection.introspection
        indexes = introspection.get_constraints(
            schema_editor.connection.cursor(),
            table_name,
        )
        for index_name, index_info in indexes.items():
            # the index will have old name, but will already point at new field name
            if index_info['columns'] == [new_field_name] and index_info['index'] and index_info['unique'] is False:
                new_index_name = index_name.replace(old_field_name, new_field_name)
                schema_editor.execute(f'ALTER INDEX {index_name} RENAME TO {new_index_name}')
                break
        
    def database_forwards(self, app_label: Any, schema_editor: Any, from_state: Any, to_state: Any) -> None:
        table_name = to_state.apps.get_model(app_label, self.model_name)._meta.db_table
        self.rename_index(schema_editor, table_name, self.old_field_name, self.new_field_name)

    def database_backwards(self, app_label: Any, schema_editor: Any, from_state: Any, to_state: Any) -> None:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('export_win', '0021_customerresponsetoken_created_on'),
    ]

    operations = [
        migrations.RenameField(
            model_name='win',
            old_name='export_experience',
            new_name='export_wins_export_experience',
        ),
        RenameIndexOperation(
            model_name='win',
            old_field_name='export_experience_id',
            new_field_name='export_wins_export_experience_id',
        ),
        migrations.AddField(
            model_name='win',
            name='export_experience',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='wins', to='company.exportexperience'),
        ),
    ]
