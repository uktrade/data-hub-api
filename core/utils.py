from django.contrib.auth.models import User
from django.db.models import ForeignKey, ManyToManyField


def generate_enum_code_from_constant_model(model_queryset):
    """Generate the Enum code for a given constant model queryset.

    Paste the generated text into the constants file.
    """

    for q in model_queryset:
        print("{} = Constant('{}', '{}')".format(q.name.replace(' ', '_').lower(), q.name, q.id))


def model_to_dictionary(model_instance, fk_ids=False):
    """Convert a model instance to a dictionary, expanding FKs and discarding M2Ms.

    :param fk_ids: If True it converts the FKs into this format 'country_id'=1
                   If False it converts the FKs into this format 'country'='United Kingdom'
    """
    data = {}
    for field in model_instance._meta.fields:
        if isinstance(field, ForeignKey):
            field_value = getattr(model_instance, field.name)
            if fk_ids:
                data[field.name+'_id'] = str(field_value.id) if field_value else None
            else:
                data[field.name] = field_value.name if field_value else None
        elif isinstance(field, ManyToManyField):
            pass
        else:
            data[field.name] = getattr(model_instance, field.name)
    return data


def get_korben_user():
    """Get or return the Korbne user."""

    korben, _ = User.objects.get_or_create(username='Korben')
    return korben

