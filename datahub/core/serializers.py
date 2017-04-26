from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.fields import UUIDField


class ConstantModelSerializer(serializers.Serializer):
    """Constant models serializer."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    selectable = serializers.BooleanField()

    class Meta:  # noqa: D101
        fields = '__all__'


class NestedRelatedField(serializers.RelatedField):
    """TODO."""
    default_error_messages = {
        'required': 'This field is required.',
        'missing_pk': 'pk not provided.',
        'does_not_exist': 'Invalid pk "{pk_value}" - object does not exist.',
        'incorrect_type': 'Incorrect type. Expected object, received {'
                          'data_type}.',
    }

    def __init__(self, model, extra_fields=('name',), **kwargs):
        super().__init__(**kwargs)
        self.pk_field = UUIDField()
        self._fields = extra_fields
        self._model = model

    def get_queryset(self):
        return self._model.objects.all()

    def to_internal_value(self, data):
        try:
            data = self.pk_field.to_internal_value(data['id'])
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except KeyError:
            self.fail('missing_pk')
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        extra = {field: _value_for_json(getattr(value, field)) for field in self._fields}
        return {
            'id': self.pk_field.to_representation(value.pk),
            **extra
        }


def _value_for_json(val):
    if isinstance(val, UUID):
        return str(val)
    return val
