from functools import partial

from dateutil.parser import parse as dateutil_parse
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField, UUIDField

from datahub.core.validate_utils import DataCombiner
from datahub.metadata.models import Country

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


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
                serializer_class=self.__class__.__name__,
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
        :param extra_fields:    List of extra fields to include in the representation.
                                Can contain field names as strings or as tuples of
                                (field name, DRF field).
                                E.g. ['field1', ('field2', CharField())]
        :param kwargs:          Keyword arguments to pass to
                                RelatedField.__init__()
        """
        super().__init__(**kwargs)

        model_class = (apps.get_model(model) if isinstance(model, str) else
                       model)

        self.pk_field = UUIDField()
        self._fields = [
            field if isinstance(field, tuple) else (field, ReadOnlyField())
            for field in extra_fields
        ]
        self._model = model_class

    def get_queryset(self):
        """Returns the queryset corresponding to the model."""
        return self._model.objects.all()

    def to_internal_value(self, data):
        """Converts a user-provided value to a model instance."""
        try:
            id_repr = data if isinstance(data, str) else data['id']
            data = self.pk_field.to_internal_value(id_repr)
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except KeyError:
            self.fail('missing_pk')
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    @staticmethod
    def get_field_value(obj, field_name):
        """Returns the field's value.

        If the field is an instance of models.Manager, then it queries
        all related objects.
        """
        value = getattr(obj, field_name)
        if isinstance(value, models.Manager):
            return value.all()

        return value

    def to_representation(self, value):
        """Converts a model instance to a dict representation."""
        if not value:
            return value

        extra = {
            field_name: field.to_representation(self.get_field_value(value, field_name))
            for field_name, field in self._fields
        }
        return {
            **extra,
            'id': self.pk_field.to_representation(value.pk),
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
                self.display_value(item),
            )
            for item in queryset
        )


RelaxedDateField = partial(serializers.DateField, input_formats=('iso-8601', '%Y/%m/%d'))


class RelaxedDateTimeField(serializers.Field):
    """
    Relaxed DateTime field.

    Front end uses free text field for data filters, that's why
    we need to accept date/datetime in various different formats.
    DRF DateTimeField doesn't offer that flexibility.
    """

    default_error_messages = {
        'invalid': 'Date is in incorrect format.',
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


class _Choices:
    """Wrapper for choices to make them compatible with DRF."""

    def __init__(self, choices):
        self._choices = choices

    def items(self):
        """Returns the choices."""
        return self._choices


class AddressSerializer(serializers.ModelSerializer):
    """
    ModelSerializer that can be used to simulate nested address objects.

    E.g.

    Model:
        class MultiAddressModel(models.Model):
            primary_address_1 = models.CharField(max_length=MAX_LENGTH)
            primary_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True)
            primary_address_town = models.CharField(max_length=MAX_LENGTH)
            primary_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
            primary_address_country = models.ForeignKey(
                Country, on_delete=models.PROTECT, related_name='+',
            )
            primary_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

            secondary_address_1 = models.CharField(max_length=MAX_LENGTH, blank=True)
            secondary_address_2 = models.CharField(max_length=MAX_LENGTH, blank=True, null=True)
            secondary_address_town = models.CharField(max_length=MAX_LENGTH, blank=True)
            secondary_address_county = models.CharField(max_length=MAX_LENGTH, blank=True)
            secondary_address_country = models.ForeignKey(
                Country, null=True, on_delete=models.SET_NULL, related_name='+',
            )
            secondary_address_postcode = models.CharField(max_length=MAX_LENGTH, blank=True)

    Serializer:
        class MultiAddressModelSerializer(serializers.ModelSerializer):
            primary_address = AddressSerializer(
                source_model=MultiAddressModel,
                address_source_prefix='primary_address',
            )
            secondary_address = AddressSerializer(
                source_model=MultiAddressModel,
                address_source_prefix='secondary_address',
                required=False,
                allow_null=True,
            )

            class Meta:
                model = MultiAddressModel
                fields = ['primary_address', 'secondary_address']

    Will produce the following API response:
        {
            'primary_address': {
                'line_1': '2',
                'line_2': '',
                'town': 'London',
                'county': '',
                'postcode': '',
                'country': {
                    'id': '80756b9a-5d95-e211-a939-e4115bead28a',
                    'name': 'United Kingdom',
                },
            },
            'secondary_address': {
                'line_1': '1',
                'line_2': '',
                'town': 'Muckamore',
                'county': '',
                'postcode': '',
                'country': {
                    'id': '736a9ab2-5d95-e211-a939-e4115bead28a',
                    'name': 'Ireland',
                },
            },
        },

    Please note:
    1. None values for CharFields will be converted to ''
    2. If all address field values are blank the nested object in the response will return None

        E.g. Fiven the following fields' values:
            secondary_address_1=''
            secondary_address_2=''
            secondary_address_town=''
            secondary_address_county=''
            secondary_address_postcode=''
            secondary_address_country_id=None

        The equivalent API response body will be:
            'secondary_address': None

        The same applies for changing the data.
    3. If AddressSerializer has required=False, the validation is triggered only if at least
        one of the fields is passed in.
    """

    line_1 = serializers.CharField(
        max_length=MAX_LENGTH,
        allow_blank=True,
        required=False,
        default='',
        source='{source_prefix}_1',
    )
    line_2 = serializers.CharField(
        max_length=MAX_LENGTH,
        allow_blank=True,
        required=False,
        default='',
        source='{source_prefix}_2',
    )
    town = serializers.CharField(
        max_length=MAX_LENGTH,
        allow_blank=True,
        required=False,
        default='',
        source='{source_prefix}_town',
    )
    county = serializers.CharField(
        max_length=MAX_LENGTH,
        allow_blank=True,
        required=False,
        default='',
        source='{source_prefix}_county',
    )
    postcode = serializers.CharField(
        max_length=MAX_LENGTH,
        allow_blank=True,
        required=False,
        default='',
        source='{source_prefix}_postcode',
    )
    country = NestedRelatedField(
        Country,
        allow_null=True,
        required=False,
        source='{source_prefix}_country',
    )

    REQUIRED_FIELDS = (
        'line_1',
        'town',
        'country',
    )

    def __init__(self, source_model, *args, address_source_prefix='address', **kwargs):
        """
        Initialises the serializer.

        It populates all necessary parts (e.g. Meta model, source, fields' source).
        """
        # Define a custom Meta so that the Meta model can be specified as an argument
        class MultiAddressMeta(self.Meta):
            model = source_model
        self.Meta = MultiAddressMeta

        kwargs.setdefault('source', '*')

        super().__init__(*args, **kwargs)

        # populate fields' source
        for field_name, field in self.fields.items():
            field.source = field.source.format(source_prefix=address_source_prefix)
            field.source_attrs = field.source.split('.')

    def run_validation(self, data=serializers.empty):
        """
        Converts None to dict with default values so that those values can be used to
        reset the fields on the model.
        """
        if data or not self.allow_null:
            normalised_data = data
        else:
            normalised_data = {
                field_name: None if (field.default == serializers.empty) else field.default
                for field_name, field in self.fields.items()
            }
        return super().run_validation(data=normalised_data)

    def to_representation(self, value):
        """
        It returns None if none of the address values is set.
        E.g.
        {
            'address': None
        }
        instead of
        {
            'address': {
                'line_1': '',
                'line_2': '',
                'town': '',
                'county': '',
                'postcode': '',
                'country': None
            }
        }
        """
        address_dict = super().to_representation(value)
        if not any(address_dict.values()):
            return None

        # for each address field, replace None with default if possible
        for field_name, value in address_dict.items():
            field_default = self.fields[field_name].default

            if value is None and field_default is not serializers.empty:
                address_dict[field_name] = field_default

        return address_dict

    def should_validate(self, data_combiner):
        """
        Returns true if the data should be validated.
        """
        if self.required:
            return True

        return any(
            data_combiner.get_value(field.source)
            for field in self.fields.values()
        )

    def validate(self, attrs):
        """
        Validates the data if necessary.
        This is needed because some addresses only need to be validated
        if they are passed in.
        """
        validated_data = super().validate(attrs)

        data_combiner = DataCombiner(self.parent.instance, validated_data)
        if self.should_validate(data_combiner):
            errors = {}
            for field_name in self.REQUIRED_FIELDS:
                field = self.fields[field_name]
                value = data_combiner.get_value(field.source)
                if not value:
                    errors[field_name] = self.error_messages['required']

            if errors:
                raise ValidationError(errors)

        return validated_data

    class Meta:
        """Meta options."""

        model = None
        fields = (
            'line_1',
            'line_2',
            'town',
            'county',
            'postcode',
            'country',
        )
