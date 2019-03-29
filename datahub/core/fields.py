from django import forms
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _


class MultipleChoiceField(ArrayField):
    """
    Simple multi-select choice field.

    This has basic validation (suitable for use in the admin site), and uses a
    MultipleChoiceField as the default form field.

    A PostgreSQL-specific ArrayField is used for the implementation. (An alternative
    implementation could use a JSONField, storing an object with keys but null values,
    however this would result in a far more complex implementation.)
    """

    default_error_messages = {
        'item_duplicated': _('An item was specified more than once.'),
    }
    default_widget = forms.CheckboxSelectMultiple

    def __init__(self, max_length=None, choices=None, **kwargs):
        """Initialises the field."""
        super().__init__(
            **kwargs,
            base_field=models.CharField(max_length=max_length, choices=choices),
        )

    def contribute_to_class(self, cls, name, private_only=False):
        """
        Injects a method into the model that returns a display-formatted version of the
        value for the field.
        """
        super().contribute_to_class(cls, name, private_only=False)

        def _get_display(obj):
            return _format_choices_for_obj(
                obj,
                choices=self.base_field.flatchoices,
                field=self,
            )

        _get_display.short_description = capfirst(self.verbose_name)
        _get_display.admin_order_field = self.attname

        setattr(cls, f'get_{self.name}_display', _get_display)

    def deconstruct(self):
        """
        Returns a 4-tuple used by makemigrations to recreate the field.

        Uses the base class of ArrayField as initialisation of ArrayField is internal to
        __init__().

        Note that choices must be converted to a tuple in order for the makemigrations change
        detection to work correctly.
        """
        name, path, args, kwargs = super(ArrayField, self).deconstruct()
        kwargs = {
            'max_length': self.base_field.max_length,
            'choices': tuple(self.base_field.choices),
            **kwargs,
        }
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        """Returns a MultipleChoiceField instance as the default form field."""
        field_kwargs = {
            'widget': self.default_widget,
            **kwargs,
        }
        return super(ArrayField, self).formfield(
            form_class=forms.MultipleChoiceField,
            choices=self.base_field.choices,
            **field_kwargs,
        )

    def validate(self, value, model_instance):
        """Performs validation, checking if any choices have been specified more than once."""
        super().validate(value, model_instance)
        if len(value) != len(frozenset(value)):
            raise ValidationError(
                self.error_messages['item_duplicated'],
                code='item_duplicated',
            )


def _format_choices_for_obj(obj, choices, field):
    choices_dict = dict(choices)
    return ', '.join(choices_dict.get(val, val) for val in getattr(obj, field.attname))
