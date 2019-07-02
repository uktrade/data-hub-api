import json
from functools import wraps
from urllib.parse import urlencode

from django import forms
from django.contrib import admin, messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.views.main import TO_FIELD_VAR
from django.core.exceptions import ValidationError
from django.core.files.uploadhandler import FileUploadHandler, SkipFile
from django.template.defaultfilters import date as date_filter, filesizeformat, time as time_filter
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy
from django.views.decorators.csrf import csrf_exempt, csrf_protect


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


class RawIdWidget(forms.TextInput):
    """
    A widget for selecting a model object using a change list in a pop-up window.

    This is similar to and based on RawForeignKeyIdWidget, however it is not tied to a
    particular model field (as RawForeignKeyIdWidget is).
    """

    template_name = 'admin/widgets/foreign_key_raw_id.html'

    def __init__(self, model, admin_site=admin.site, attrs=None):
        """Initialises the widget."""
        self.model = model
        self.admin_site = admin_site
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        """Gets the template context."""
        context = super().get_context(name, value, attrs)

        if self.model not in self.admin_site._registry:
            raise ValueError('The specified model is not registered with the specified admin site')

        changelist_route_name = admin_urlname(self.model._meta, 'changelist')

        related_url = reverse(changelist_route_name, current_app=self.admin_site.name)
        params = {
            TO_FIELD_VAR: 'id',
        }
        query_string = urlencode(params)

        context['related_url'] = f'{related_url}?{query_string}'
        context['widget']['attrs']['class'] = 'vForeignKeyRawIdAdminField'

        title_format = gettext('Look up {verbose_name}')
        context['link_title'] = title_format.format(verbose_name=self.model._meta.verbose_name)

        if context['widget']['value']:
            context['link_label'], context['link_url'] = self.label_and_url_for_value(value)

        return context

    def label_and_url_for_value(self, value):
        """Gets the link label and URL for a specified value."""
        try:
            obj = self.model.objects.get(pk=value)
        except (ValueError, self.model.DoesNotExist, ValidationError):
            return '', ''

        change_route_name = admin_urlname(obj._meta, 'change')
        url = reverse(change_route_name, args=(obj.pk,), current_app=self.admin_site.name)

        return str(obj), url


class MaxSizeFileUploadHandler(FileUploadHandler):
    """
    File upload handler that stops uploads that exceed a certain size.

    This aborts the process before the file has been loaded into memory or saved to disk.

    It is useful for protection against large files being uploaded and filling up
    temporary file storage space (when using the default upload handlers).

    You will probably want to use the max_upload_size decorator rather than using
    this class directly.
    """

    FILE_TOO_LARGE_MESSAGE = gettext_lazy(
        'The file {file_name} was too large. Files must be less than {max_size}.',
    )

    def __init__(self, request, max_size):
        """Initialises the handler with a request and maximum size."""
        super().__init__(request)
        self.max_size = max_size

    def receive_data_chunk(self, raw_data, start):
        """Checks if a chunk of data will take the upload over the limit."""
        if start + len(raw_data) > self.max_size:
            formatted_file_size = filesizeformat(self.max_size)
            error_msg = self.FILE_TOO_LARGE_MESSAGE.format(
                file_name=self.file_name,
                max_size=formatted_file_size,
            )
            django_messages.error(self.request, error_msg)

            raise SkipFile()
        return raw_data

    def file_complete(self, file_size):
        """Does nothing, so that the next handler processes the upload."""


def max_upload_size(max_size):
    """
    View decorator to enforce a maximum size on uploads.

    Note: If you want to make a view exempt from CSRF protection, you must ensure that
    the @csrf_exempt decorator is applied first. For example::

        @max_upload_size(...)
        @csrf_exempt
        def view():
            ...
    """
    def decorator(view_func):
        @csrf_exempt
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Note: request.upload_handlers must be manipulated before CSRF-protection
            # routines run
            request.upload_handlers.insert(0, MaxSizeFileUploadHandler(request, max_size))
            return csrf_protect(view_func)(request, *args, **kwargs)

        return wrapped_view

    return decorator


def custom_view_permission(permission_codename):
    """
    Decorator that allows a custom view permission to be used with ModelAdmin subclasses.

    Usage example::

        @admin.register(InvestmentProject)
        @custom_view_permission('view_all_investmentproject')
        class InvestmentProjectAdmin(admin.ModelAdmin):
            pass
    """
    def decorator(admin_cls):
        admin_cls.has_view_permission = _make_admin_permission_getter(permission_codename)
        return admin_cls

    return decorator


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


def format_json_as_html(value):
    """
    Serialises an object as pretty JSON, and HTML-encodes it in a <pre> tag.

    This is useful for displaying JSON fields in the admin site.

    Usage example:

        class InteractionAdmin(ModelAdmin):
            readonly_fields = (
                # also make sure source is not included
                'pretty_source',
            )

            def pretty_source(self, obj):
                return format_json_as_html(obj.source)

            pretty_source.short_description = 'source'

    """
    return format_html('<pre>{0}</pre>', json.dumps(value, indent=2))


def _make_admin_permission_getter(codename):
    def _has_permission(self, request, obj=None):
        app_label = self.opts.app_label
        qualified_name = f'{app_label}.{codename}'
        return request.user.has_perm(qualified_name)

    return _has_permission
