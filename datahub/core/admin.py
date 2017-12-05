from collections import OrderedDict

from django.contrib import admin
from reversion.admin import VersionAdmin


class DisabledOnFilter(admin.SimpleListFilter):
    """This filter allows us to filter values that have disabled_on value."""

    title = 'Is disabled'
    parameter_name = 'disabled_on'

    def lookups(self, request, model_admin):
        """Returns parameters."""
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        """Modify query according to filter parameter."""
        value = self.value()
        if value is not None:
            is_disabled = True if value == 'yes' else False
            return queryset.filter(disabled_on__isnull=(not is_disabled))
        return queryset


class ConfigurableVersionAdmin(VersionAdmin):
    """
    Subclass of VersionAdmin that allows the excluded model fields for django-reversion
    to be easily set.

    This is in line with the example on:
    https://django-reversion.readthedocs.io/en/stable/admin.html#reversion-admin-versionadmin

    Excluded fields are not saved in django-reversion versions.

    This is set in the admin class because we're using django-reversion auto-registration
    via VersionAdmin.
    """

    reversion_excluded_fields = None

    def reversion_register(self, model, **options):
        """Used the the django-reversion model auto-registration mechanism."""
        if self.reversion_excluded_fields:
            options['exclude'] = self.reversion_excluded_fields
        super().reversion_register(model, **options)


class BaseModelVersionAdmin(ConfigurableVersionAdmin):
    """
    VersionAdmin subclass that excludes fields defined on BaseModel.

    These aren't particularly useful to save in django-reversion versions because
    created_by/created_on will not change between versions, and modified_on/modified_by
    is tracked by django-reversion separately in revisions.
    """

    reversion_excluded_fields = ('created_on', 'created_by', 'modified_on', 'modified_by')


class ReadOnlyAdmin(admin.ModelAdmin):
    """ModelAdmin subclass that makes models viewable but not editable."""

    def has_add_permission(self, request, obj=None):
        """
        Gets whether the user can add new objects for this model.

        Always returns False.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Gets whether the user can delete objects for this model.

        Always returns False.
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        Gets the read-only fields for this model.

        Always returns all fields.
        """
        # OrderedDict used instead of set to preserve order
        readonly_fields = list(OrderedDict.fromkeys(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))

        if 'is_submitted' in readonly_fields:
            readonly_fields.remove('is_submitted')
        return readonly_fields
