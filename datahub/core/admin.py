from collections import OrderedDict

from django.contrib import admin


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
        # if reaonly_fields defined explicitly, use that
        if self.readonly_fields:
            return self.readonly_fields

        # OrderedDict used instead of set to preserve order
        readonly_fields = list(OrderedDict.fromkeys(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))

        if 'is_submitted' in readonly_fields:
            readonly_fields.remove('is_submitted')
        return readonly_fields


def custom_add_permission(permission_codename):
    """
    Decorator that allows a custom add permission to be used with ModelAdmin subclasses.

    Usage example::

        @admin.register(InvestmentProject)
        @custom_change_permission('add_custom_investmentproject')
        class InvestmentProjectAdmin(admin.ModelAdmin):
            pass
    """
    def decorator(admin_cls):
        admin_cls.has_add_permission = _make_admin_permission_getter(permission_codename)
        return admin_cls

    return decorator


def custom_change_permission(permission_codename):
    """
    Decorator that allows a custom change permission to be used with ModelAdmin subclasses.

    Usage example::

        @admin.register(InvestmentProject)
        @custom_change_permission('change_all_investmentproject')
        class InvestmentProjectAdmin(admin.ModelAdmin):
            pass
    """
    def decorator(admin_cls):
        admin_cls.has_change_permission = _make_admin_permission_getter(permission_codename)
        return admin_cls

    return decorator


def custom_delete_permission(permission_codename):
    """
    Decorator that allows a custom delete permission to be used with ModelAdmin subclasses.

    Usage example::

        @admin.register(InvestmentProject)
        @custom_delete_permission('delete_all_investmentproject')
        class InvestmentProjectAdmin(admin.ModelAdmin):
            pass
    """
    def decorator(admin_cls):
        admin_cls.has_delete_permission = _make_admin_permission_getter(permission_codename)
        return admin_cls

    return decorator


def _make_admin_permission_getter(codename):
    def _has_permission(self, request, obj=None):
        app_label = self.opts.app_label
        qualified_name = f'{app_label}.{codename}'
        return request.user.has_perm(qualified_name)

    return _has_permission
