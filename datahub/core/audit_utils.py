from django.core.exceptions import ValidationError
from django.db import models


def diff_versions(model_meta, old_version, new_version):
    """
    Audit versions comparision with the delta returned.

    For related objects only the pk is stored in the audit history.
    A user friendly representation of the related object (the object name)
    is retrieved if the relationship still exists.

    """
    friendly_changes = {}
    raw_changes = _get_changes(old_version, new_version)

    for db_field_name, values in raw_changes.items():
        field = _get_field_or_none(model_meta, db_field_name)
        field_name = field.name if field else db_field_name
        friendly_changes[field_name] = [_make_value_friendly(field, value) for value in values]
    return friendly_changes


def _get_changes(old_version, new_version):
    """Compares dictionaries returning the delta between them."""
    changes = {}

    for field_name, new_value in new_version.items():
        if field_name not in old_version:
            changes[field_name] = [None, new_value]
        else:
            old_value = old_version[field_name]
            if _are_values_different(old_value, new_value):
                changes[field_name] = [old_value, new_value]
    return changes


def _are_values_different(old_value, new_value):
    """Checks if the two values are different whilst treating a blank string the same as a None."""
    old_value = old_value if old_value != '' else None
    new_value = new_value if new_value != '' else None
    return old_value != new_value


def _get_field_or_none(model_meta, db_column_name):
    """Gets a model field for a given model meta, if the field cannot be found returns None."""
    try:
        return model_meta.get_field(db_column_name)
    except models.FieldDoesNotExist:
        return None


def _make_value_friendly(field, value):
    """
    Checks field and if required retrieves the object name from related model.

    If the field is None or not a related field then the value can be
    returned as the value is not an object pk.

    For related objects the object name is then retrieved, for many to many and
    one to many all values need to be retrieved individually.

    """
    if not field or not field.is_relation:
        return value

    if field.many_to_many or field.one_to_many:
        return [
            _get_object_name_for_pk(
                field.related_model, one_value,
            ) for one_value in value
        ]
    return _get_object_name_for_pk(field.related_model, value)


def _get_object_name_for_pk(model, pk):
    """
    Gets the name for a given object pk or returns the pk if it cannot be found.
    """
    try:
        result = model.objects.get(pk=pk)
    except (model.DoesNotExist, ValueError, TypeError, ValidationError):
        return pk
    return str(result)
