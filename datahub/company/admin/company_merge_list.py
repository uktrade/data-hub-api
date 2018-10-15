from logging import getLogger

from django.contrib import messages as django_messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters, admin_urlname
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
from django.views.decorators.csrf import csrf_protect

from datahub.feature_flag.utils import feature_flagged_view, is_feature_flag_active

MERGE_LIST_SESSION_KEY = 'admin-company-company-merge-list'
MERGE_LIST_FEATURE_FLAG = 'admin-merge-company-tool'

logger = getLogger(__name__)


class CompanyMergeViews:
    """Views related to the merge-duplicate-companies functionality."""

    MERGE_LIST_FIELDS = (
        'id',
        'name',
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )
    ADDED_TO_MERGE_LIST_MSG = gettext_lazy(
        '1 item added to the merge list. <a href="{url}">View merge list</a>.',
    )
    ALREADY_ON_MERGE_LIST_MSG = gettext_lazy(
        'This item was already on the merge list. <a href="{url}">View merge list</a>.',
    )
    REMOVED_FROM_MERGE_LIST_MSG = gettext_lazy('1 item removed from the merge list.')

    def __init__(self, model_admin: ModelAdmin):
        """Initialises the instance, storing a reference to the relevant ModelAdmin."""
        self.model_admin = model_admin

    def get_urls(self):
        """Gets the URLs for the merge views."""
        model_meta = self.model_admin.model._meta
        admin_site = self.model_admin.admin_site
        return [
            path(
                'merge-list/',
                admin_site.admin_view(self.merge_list),
                name=f'{model_meta.app_label}_{model_meta.model_name}'
                     f'_merge-list',
            ),
            path(
                '<path:object_id>/add-to-merge-list/',
                admin_site.admin_view(self.add_to_merge_list),
                name=f'{model_meta.app_label}_{model_meta.model_name}'
                     f'_add-to-merge-list',
            ),
            path(
                '<path:object_id>/remove-from-merge-list/',
                admin_site.admin_view(self.remove_from_merge_list),
                name=f'{model_meta.app_label}_{model_meta.model_name}'
                     f'_remove-from-merge-list',
            ),
        ]

    @feature_flagged_view(MERGE_LIST_FEATURE_FLAG)
    def merge_list(self, request):
        """View listing companies that have been added to the merge list."""
        if not self.model_admin.has_change_permission(request):
            raise PermissionDenied

        template_name = 'admin/company/company/merge_list.html'
        title = 'Company merge list'

        model = self.model_admin.model
        admin_site = self.model_admin.admin_site

        company_pks = _get_pks_from_merge_list_store(request)
        merge_items_gen = (model.objects.filter(pk=pk).first() for pk in company_pks)
        merge_items = {
            str(obj.pk): [getattr(obj, field) for field in self.MERGE_LIST_FIELDS]
            for obj in merge_items_gen if obj
        }

        columns = {
            field: model._meta.get_field(field).verbose_name for field in self.MERGE_LIST_FIELDS
        }

        context = {
            **admin_site.each_context(request),
            'opts': model._meta,
            'title': title,
            'columns': columns,
            'merge_items': merge_items,
        }
        return TemplateResponse(request, template_name, context)

    @method_decorator(csrf_protect)
    @feature_flagged_view(MERGE_LIST_FEATURE_FLAG)
    def add_to_merge_list(self, request, object_id):
        """View handling additions to the merge list."""
        if not self.model_admin.has_change_permission(request):
            raise PermissionDenied

        model_meta = self.model_admin.model._meta
        was_added = _add_pk_to_merge_list_store(request, object_id)

        route_name = admin_urlname(model_meta, 'merge-list')
        merge_list_url = reverse(route_name, current_app=self.model_admin.admin_site.name)

        msg_template = (
            self.ADDED_TO_MERGE_LIST_MSG if was_added else self.ALREADY_ON_MERGE_LIST_MSG
        )
        msg = format_html(msg_template, url=merge_list_url)
        self.model_admin.message_user(request, msg, django_messages.SUCCESS)

        return _changelist_preserved_filters_redirect(request, self.model_admin)

    @method_decorator(csrf_protect)
    @feature_flagged_view(MERGE_LIST_FEATURE_FLAG)
    def remove_from_merge_list(self, request, object_id):
        """View handling removals from the merge list."""
        if not self.model_admin.has_change_permission(request):
            raise PermissionDenied

        _remove_pk_from_merge_list_store(request, object_id)

        model_meta = self.model_admin.model._meta
        route_name = admin_urlname(model_meta, 'merge-list')
        merge_list_url = reverse(route_name, current_app=self.model_admin.admin_site.name)

        self.model_admin.message_user(
            request,
            self.REMOVED_FROM_MERGE_LIST_MSG,
            django_messages.SUCCESS,
        )

        return HttpResponseRedirect(merge_list_url)

    @staticmethod
    def changelist_context(request):
        """Returns additional context data for the change list view."""
        merge_list = _get_pks_from_merge_list_store(request)
        return {
            'merge_list_count': len(merge_list),
            'merge_list_feature_flag': is_feature_flag_active(MERGE_LIST_FEATURE_FLAG),
        }

    @staticmethod
    def change_context(request):
        """Returns additional context data for the change view."""
        return {
            'merge_list_feature_flag': is_feature_flag_active(MERGE_LIST_FEATURE_FLAG),
        }


def _get_pks_from_merge_list_store(request):
    try:
        return list(request.session.get(MERGE_LIST_SESSION_KEY, []))
    except TypeError:
        logger.warning('Corrupt merge list detected in session')
        return []


def _add_pk_to_merge_list_store(request, pk):
    merge_list = _get_pks_from_merge_list_store(request)
    pk_str = str(pk)
    if pk_str not in merge_list:
        merge_list.append(pk_str)
        request.session[MERGE_LIST_SESSION_KEY] = merge_list
        return True
    return False


def _remove_pk_from_merge_list_store(request, pk):
    merge_list = _get_pks_from_merge_list_store(request)
    pk_str = str(pk)
    try:
        merge_list.remove(pk_str)
    except ValueError:
        return False

    request.session[MERGE_LIST_SESSION_KEY] = merge_list
    return True


def _changelist_preserved_filters_redirect(request, model_admin):
    model_meta = model_admin.model._meta
    route_name = admin_urlname(model_meta, 'changelist')
    changelist_url = reverse(route_name, current_app=model_admin.admin_site.name)

    preserved_filters = model_admin.get_preserved_filters(request)
    filtered_changelist_url = add_preserved_filters(
        {
            'preserved_filters': preserved_filters,
            'opts': model_meta,
        },
        changelist_url,
    )

    return HttpResponseRedirect(filtered_changelist_url)
