from django.contrib.auth.backends import ModelBackend, get_user_model
from django.db.models import ForeignKey, ManyToManyField


def generate_enum_code_from_constant_model(model_queryset):
    """Generate the Enum code for a given constant model queryset.

    Paste the generated text into the constants file.
    """
    for q in model_queryset:
        print("{} = Constant('{}', '{}')".format(q.name.replace(' ', '_').lower(), q.name, q.id))


def _handle_fk(field_name, field_value, fk_ids):
    """Handle FK conversion to dict.

    :param fk_ids: If True it converts the FKs into this format 'country_id'=1
                   If False it converts the FKs into this format 'country'='United Kingdom'
    """
    if fk_ids:
        return field_name + '_id', str(field_value.id) if field_value else None
    else:
        return field_name, getattr(field_value, 'name', None) if field_value else None


def model_to_dictionary(model_instance, excluded_fields=(), fk_ids=False):
    """Convert a model instance to a dictionary, expanding FKs and discarding M2Ms.

    :param fk_ids: If True it converts the FKs into this format 'country_id'=1
                   If False it converts the FKs into this format 'country'='United Kingdom'
    """
    data = {}

    for field in [field for field in model_instance._meta.fields if field.name not in excluded_fields]:
        if isinstance(field, ForeignKey):
            field_value = getattr(model_instance, field.name)
            key, value = _handle_fk(field.name, field_value, fk_ids)
            data[key] = value
        elif isinstance(field, ManyToManyField):
            pass
        else:
            data[field.name] = getattr(model_instance, field.name)
    return data


class CDMSUserBackend(ModelBackend):
    """Model backend that authenticates against CDMS,
    but still uses and provides core django functionality."""

    def korben_authenticate(self, **kwargs):
        """Authenticate CDMS user/advisor using korben."""
        raise NotImplementedError()

    def authenticate(self, username=None, password=None, **kwargs):
        """Copied from parent impl, but with password check done by Korben."""
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if (
                    self.korben_authenticate(
                        username=username, password=password)
                    and self.user_can_authenticate(user)
            ):
                return user
