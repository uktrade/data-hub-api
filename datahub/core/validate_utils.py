from functools import lru_cache
from typing import Sequence

from rest_framework.utils import model_meta


class DataCombiner:
    """
    Combines values from the dict of updated data and the model instance fields.
    Its methods return the first value found in the chain (update_data, instance).

    Used for cross-field validation of v3 endpoints (because PATCH requests
    will only contain data for fields being updated).
    """

    def __init__(self, instance, update_data, serializer=None, model=None):
        """Initialises the combiner."""
        if instance is None and update_data is None:
            raise TypeError('One of instance and update_data must be provided '
                            'and not None')

        if update_data is None:
            update_data = {}

        self.instance = instance
        self.data = update_data
        self.serializer = serializer
        self.model = model

    def __getitem__(self, item):
        """Returns the value of a field, using get_value_auto()."""
        return self.get_value_auto(item)

    def get_value_auto(self, field_name):
        """
        Returns the value of a field (returning the ID for foreign keys).

        Automatically calls get_value(), get_value_to_many() or get_value_id() depending on the
        field type.

        Requires the model class to be available.
        """
        field_info = _get_model_field_info(self.model)

        if field_name in field_info.relations:
            if field_info.relations[field_name].to_many:
                value = self.get_value_to_many(field_name)
            else:
                value = self.get_value_id(field_name)
        else:
            value = self.get_value(field_name)

        return value

    def get_value(self, field_name):
        """Returns the value of a standard field."""
        if field_name in self.data:
            return self.data[field_name]
        if self.instance:
            return getattr(self.instance, field_name)
        return None

    def get_value_to_many(self, field_name):
        """Returns an object representing to-many field values."""
        if field_name in self.data:
            return self.data[field_name]
        if self.instance:
            return getattr(self.instance, field_name).all()
        return ()

    def get_value_id(self, field_name):
        """Returns the ID of foreign keys."""
        value = self.get_value(field_name)
        return str(value.id) if value else None


def is_blank(value):
    """Returns True if a value is considered empty or blank."""
    return value in (None, '') or (isinstance(value, Sequence) and len(value) == 0)


def is_not_blank(value):
    """Returns True if a value is not considered empty or blank."""
    return not is_blank(value)


@lru_cache()
def _get_model_field_info(model):
    return model_meta.get_field_info(model)
