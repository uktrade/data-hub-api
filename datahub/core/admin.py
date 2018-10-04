from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.template.defaultfilters import date as date_filter, time as time_filter
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


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


class ViewAndChangeOnlyAdmin(admin.ModelAdmin):
    """ModelAdmin subclass that restricts adding and deletion at all times."""

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


class ViewOnlyAdmin(ViewAndChangeOnlyAdmin):
    """
    ModelAdmin subclass that restricts adding, changing and deleting at all times.

    The user must have the relevant view or change permission in order to be able to view the
    model.
    """

    def has_change_permission(self, request, obj=None):
        """
        Gets whether the user can change objects for this model.

        Always returns False.
        """
        return False


class BaseModelAdminMixin:
    """
    Mixin for ModelAdmins which adds extra functionalities.
    Useful when the model extends core.BaseModel

    It updates created_by and modified_by automatically from the logged in user.

    It also adds support for descriptive versions of created_on/by and modified_on/by,
    using only two admin "fields": 'created' and 'modified'.
    To use them just add 'created' and 'modified' to `readonly_fields` and `fields`
    instead of created_on/by and modified_on/by.
    """

    def _get_description_for_timed_event(self, event_on, event_by):
        text_parts = []
        if event_on:
            text_parts.extend((
                f'on {date_filter(event_on)}',
                f'at {time_filter(event_on)}',
            ))
        if event_by:
            adviser_admin_url = get_change_link(event_by)
            text_parts.append(f'by {adviser_admin_url}')

        return mark_safe(' '.join(text_parts) or '-')

    def created(self, obj):
        """:returns: created on/by details."""
        return self._get_description_for_timed_event(obj.created_on, obj.created_by)

    def modified(self, obj):
        """:returns: modified on/by details."""
        return self._get_description_for_timed_event(obj.modified_on, obj.modified_by)

    def save_model(self, request, obj, form, change):
        """
        Populate created_by/modified_by from the logged in user.
        """
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user

        super().save_model(request, obj, form, change)


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


def get_change_url(obj, site=admin.site):
    """Returns the URL to the admin change page for an object."""
    if not obj or not obj.pk:
        return ''

    return reverse(admin_urlname(obj._meta, 'change'), args=(obj.pk,), current_app=site.name)


def get_change_link(obj, site=admin.site):
    """Returns a link to the admin change page for an object."""
    url = get_change_url(obj, site=site)

    if not url:
        return ''

    return format_html('<a href="{url}">{name}</a>'.format(url=url, name=obj))


def _make_admin_permission_getter(codename):
    def _has_permission(self, request, obj=None):
        app_label = self.opts.app_label
        qualified_name = f'{app_label}.{codename}'
        return request.user.has_perm(qualified_name)

    return _has_permission
