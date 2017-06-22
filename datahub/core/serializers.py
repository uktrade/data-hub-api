from uuid import UUID

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.fields import UUIDField


class ConstantModelSerializer(serializers.Serializer):
    """Constant models serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()

    class Meta:  # noqa: D101
        fields = '__all__'


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
