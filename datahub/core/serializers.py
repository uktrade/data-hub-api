from uuid import UUID

from dateutil.parser import parse as dateutil_parse
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.fields import UUIDField


class ConstantModelSerializer(serializers.Serializer):
    """Constant models serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    disabled_on = serializers.ReadOnlyField()


class PermittedFieldsModelSerializer(serializers.ModelSerializer):
    """Lets you get permitted fields only.

    Needs 'permissions' attribute on Meta class in following format:
        permissions = {
            'app_name.permission': 'field'
        }

    If user doesn't have required permission, corresponding field will be filtered out.

    Note: The current implementation does not allow access to the field if request.user is None.
    """

    def get_fields(self):
        """Gets filtered dictionary of fields based on permissions."""
        assert hasattr(self.Meta, 'permissions'), (
            'Class {serializer_class} missing "Meta.permissions" attribute'.format(
                serializer_class=self.__class__.__name__
            )
        )

        fields = super().get_fields()
        request = self.context.get('request', None)

        if request:
            permissions = self.Meta.permissions
            for permission, field in permissions.items():
                if not request.user or not request.user.has_perm(permission):
                    del fields[field]
        return fields


class NestedRelatedField(serializers.RelatedField):
    """DRF serialiser field for foreign keys and many-to-many fields.

    Serialises as a dict with 'id' plus other specified keys.
    """

    default_error_messages = {
        'required': 'This field is required.',
        'missing_pk': 'pk not provided.',
        'does_not_exist': 'Invalid pk "{pk_value}" - object does not exist.',
        'incorrect_type': 'Incorrect type. Expected object, received {'
                          'data_type}.',
    }

    def __init__(self, model, extra_fields=('name',), **kwargs):
        """Initialises the related field.

        :param model:           Model of the related field.
        :param extra_fields:    Extra fields to include in the representation.
        :param kwargs:          Keyword arguments to pass to
                                RelatedField.__init__()
        """
        super().__init__(**kwargs)

        model_class = (apps.get_model(model) if isinstance(model, str) else
                       model)

        self.pk_field = UUIDField()
        self._fields = extra_fields
        self._model = model_class

    def get_queryset(self):
        """Returns the queryset corresponding to the model."""
        return self._model.objects.all()

    def to_internal_value(self, data):
        """Converts a user-provided value to a model instance."""
        try:
            if isinstance(data, str):
                id_repr = data
            else:
                id_repr = data['id']
            data = self.pk_field.to_internal_value(id_repr)
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except KeyError:
            self.fail('missing_pk')
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        """Converts a model instance to a dict representation."""
        extra = {field: _value_for_json(getattr(value, field)) for field in
                 self._fields}
        return {
            **extra,
            'id': self.pk_field.to_representation(value.pk)
        }

    def get_choices(self, cutoff=None):
        """Returns choices for DRF UI.

        Standard implementation uses a dict, but that doesn't work as our
        representation isn't hashable.
        """
        queryset = self.get_queryset()
        if queryset is None:
            return ()

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return _Choices(
            (
                self.pk_field.to_representation(item.pk),
                self.display_value(item)
            )
            for item in queryset
        )


class RelaxedDateTimeField(serializers.Field):
    """
    Relaxed DateTime field.

    Front end uses free text field for data filters, that's why
    we need to accept date/datetime in various different formats.
    DRF DateTimeField doesn't offer that flexibility.
    """

    default_error_messages = {
        'invalid': 'Date is in incorrect format.'
    }

    def to_internal_value(self, data):
        """Parses data into datetime."""
        try:
            data = dateutil_parse(data)
        except ValueError:
            self.fail('invalid', value=data)
        return data

    def to_representation(self, value):
        """Formats the datetime using a normal DateTimeField."""
        repr_field = serializers.DateTimeField()
        return repr_field.to_representation(value)


class RelaxedURLField(serializers.URLField):
    """URLField subclass that prepends http:// to input and output when a scheme is not present."""

    def to_internal_value(self, data):
        """Converts a user-provided value to an internal value."""
        return super().to_internal_value(self._fix_missing_url_scheme(data))

    def to_representation(self, value):
        """Converts a stored value to the external representation."""
        return super().to_representation(self._fix_missing_url_scheme(value))

    @staticmethod
    def _fix_missing_url_scheme(value):
        if value and '://' not in value:
            return f'http://{value}'
        return value


def _value_for_json(val):
    """Returns a JSON-serialisable version of a value."""
    if isinstance(val, UUID):
        return str(val)
    return val


class _Choices:
    """Wrapper for choices to make them compatible with DRF."""

    def __init__(self, choices):
        self._choices = choices

    def items(self):
        """Returns the choices."""
        return self._choices
