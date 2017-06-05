from rest_framework.exceptions import ValidationError


class OneOfValidator:
    """
    One-of validator for DRF serializer classes.

    To be used at class-level only. For updates, values from the model
    instance are used where the fields are not part of the update request.
    """

    message = 'One of {field_names} must be provided.'

    def __init__(self, *fields, message=None):
        """
        Initialises the validator.

        :param fields:  Fields to perform one-of validation on
        :param message: Optional custom error message
        """
        self.fields = fields
        self.message = message or self.message
        self.serializer = None

    def set_context(self, serializer):
        """
        Saves a reference to the serializer object.

        Called by DRF.
        """
        self.serializer = serializer

    def __call__(self, attrs):
        """
        Performs validation. Called by DRF.

        :param attrs:   Serializer data (post-field-validation/processing)
        """
        data_view = UpdatedDataView(self.serializer.instance, attrs)
        values = (data_view.get_value(field) for field in self.fields)
        value_present = any(value for value in values if value is not None)
        if not value_present:
            field_names = ', '.join(self.fields)
            message = self.message.format(field_names=field_names)
            raise ValidationError(message, code='one_of')

    def __repr__(self):
        """Returns the string representation of this object."""
        return f'{self.__class__.__name__}(fields={self.fields!r})'


class UpdatedDataView:
    """
    Provides a view of a model instance and dict of new data.

    Used for cross-field validation of v3 endpoints (because PATCH requests
    will only contain data for fields being updated).
    """

    def __init__(self, instance, update_data):
        """Initialises the view."""
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
        return None

    def get_value_id(self, field_name):
        """Returns the ID of foreign keys."""
        value = self.get_value(field_name)
        return str(value.id) if value else None
