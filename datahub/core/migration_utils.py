import logging

import yaml
from django.core.serializers import base
from django.db import DEFAULT_DB_ALIAS, transaction
from django.db.migrations.operations.models import DeleteModel

logger = logging.getLogger(__name__)


def _build_model_data(model, obj_pk, fields_data, using):
    data = {}
    # Handle each field
    for (field_name, field_value) in fields_data.items():
        field = model._meta.get_field(field_name)

        # Handle many-to-many relations
        if field.many_to_many:
            raise NotImplementedError('Many-to-many fields not supported')

        # Handle one-to-many relations
        if field.one_to_many:
            raise NotImplementedError('One-to-many fields not supported')

        # Handle fk fields
        if field.many_to_one:
            try:
                value = base.deserialize_fk_value(field, field_value, using, False)
            except Exception as exc:
                raise base.DeserializationError.WithData(
                    exc,
                    model._meta.model_name,
                    obj_pk,
                    field_value,
                ) from exc
            data[field.attname] = value
        # Handle all other fields
        else:
            try:
                data[field.name] = field.to_python(field_value)
            except Exception as exc:
                raise base.DeserializationError.WithData(
                    exc,
                    model._meta.model_name,
                    obj_pk,
                    field_value,
                ) from exc
    return data


def _load_data_in_migration(apps, object_list, using=DEFAULT_DB_ALIAS):
    for list_item in object_list:
        obj_pk = list_item.get('pk')
        assert obj_pk, 'pk field required'

        model_label = list_item['model']
        model = apps.get_model(model_label)
        fields_data = list_item['fields']

        model_data = _build_model_data(model, obj_pk, fields_data, using)
        model.objects.update_or_create(pk=obj_pk, defaults=model_data)


@transaction.atomic
def load_yaml_data_in_migration(apps, fixture_file_path):
    """
    Loads the content of the yaml file `fixture_file_path` into the database.
    This is similar to `loaddata` but:
    - it's safe to be used in migrations
    - it does not change the fields that are not present in the yaml

    Motivation:
    Calling `loaddata` from a data migration makes django use the latest version
    of the models instead of the version at the time of that particular migration.
    This causes problems e.g. adding a new field to a model which had a data migration
    in the past is okay but migrating from zero fails as the model in
    loaddata (the latest) has a field that did not exist at that migration time.

    Limitations:
    - Many-to-many fields are not supported yet
    - all items in the yaml have to include a pk field
    """
    with open(fixture_file_path, 'rb') as fixture:
        object_list = yaml.safe_load(fixture)
        _load_data_in_migration(apps, object_list)


class DeleteModelWithMetadata(DeleteModel):
    """
    When deleting a model, we have to manually delete the associated
    django permissions and django contenttypes.

    This adds deletion of associated permissions and contenttypes to
    the DeleteModel operation.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        """
        Delete permissions and contenttypes before deleting the model
        """
        DeleteModelWithMetadata.delete_metadata(
            from_state.apps,
            app_label,
            self.name,
        )
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    @staticmethod
    def delete_metadata(apps, app_label, model_name):
        """
        Delete associated permissions and contenttypes for the given model.
        """
        permission_model = apps.get_model('auth', 'Permission')
        _, deletions_by_model = permission_model.objects.filter(
            content_type__app_label=app_label,
            content_type__model=model_name,
        ).delete()
        logger.info(
            f'Deleted {app_label}.{model_name} permissions. '
            f'Breakdown of deleted objects: {deletions_by_model}',
        )

        content_type_model = apps.get_model('contenttypes', 'ContentType')
        _, deletions_by_model = content_type_model.objects.filter(
            app_label=app_label,
            model=model_name,
        ).delete()
        logger.info(
            f'Deleted {app_label}.{model_name} content types. '
            f'Breakdown of deleted objects: {deletions_by_model}',
        )
