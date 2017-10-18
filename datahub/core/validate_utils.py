from typing import Sequence


class DataCombiner:
    """
    Combines values from the dict of updated data and the model instance fields.
    Its methods return the first value found in the chain (update_data, instance).

    Used for cross-field validation of v3 endpoints (because PATCH requests
    will only contain data for fields being updated).
    """

    def __init__(self, instance, update_data):
        """Initialises the combiner."""
        if instance is None and update_data is None:
            raise TypeError('One of instance and update_data must be provided '
                            'and not None')

        if update_data is None:
            update_data = {}

        self.instance = instance
        self.data = update_data

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
