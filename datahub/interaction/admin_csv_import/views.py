from itertools import islice

from django.conf import settings
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.core.admin import max_upload_size
from datahub.feature_flag.utils import feature_flagged_view
from datahub.interaction.admin_csv_import.file_form import InteractionCSVForm
from datahub.interaction.models import Interaction, InteractionPermission

INTERACTION_IMPORTER_FEATURE_FLAG_NAME = 'admin-interaction-csv-importer'
MAX_ERRORS_TO_DISPLAY = 50
MAX_PREVIEW_ROWS_TO_DISPLAY = 100
PAGE_TITLE = gettext_lazy('Import interactions')


interaction_change_all_permission_required = method_decorator(
    permission_required(
        f'interaction.{InteractionPermission.change_all}',
        raise_exception=True,
    ),
)


class InteractionCSVImportAdmin:
    """
    Views related to importing interactions from a CSV file.

    The implementation is not yet complete; hence, views are behind a feature flag.
    """

    def __init__(self, model_admin):
        """Initialises the instance with a reference to an InteractionAdmin instance."""
        self.model_admin = model_admin

    def get_urls(self):
        """Gets a list of routes that should be registered."""
        model_meta = self.model_admin.model._meta
        admin_site = self.model_admin.admin_site

        return [
            path(
                'import',
                admin_site.admin_view(self.select_file),
                name=f'{model_meta.app_label}_{model_meta.model_name}_import',
            ),
        ]

    @feature_flagged_view(INTERACTION_IMPORTER_FEATURE_FLAG_NAME)
    @interaction_change_all_permission_required
    @method_decorator(max_upload_size(settings.INTERACTION_ADMIN_CSV_IMPORT_MAX_SIZE))
    def select_file(self, request, *args, **kwargs):
        """View containing a form to select a CSV file to import."""
        if request.method != 'POST':
            return self._select_file_form_response(request, InteractionCSVForm())

        form = InteractionCSVForm(request.POST, request.FILES)
        if not form.is_valid():
            return self._select_file_form_response(request, form)

        if not form.are_all_rows_valid():
            return self._error_list_response(request, form.get_row_error_iterator())

        return self._preview_response(request, form)

    def _select_file_form_response(self, request, form):
        return self._template_response(
            request,
            'admin/interaction/interaction/import_select_file.html',
            PAGE_TITLE,
            form=form,
        )

    def _error_list_response(self, request, errors):
        limited_errors = list(islice(errors, MAX_ERRORS_TO_DISPLAY))
        are_errors_truncated = bool(next(errors, None))

        return self._template_response(
            request,
            'admin/interaction/interaction/import_row_errors.html',
            PAGE_TITLE,
            errors=limited_errors,
            are_errors_truncated=are_errors_truncated,
            max_errors=MAX_ERRORS_TO_DISPLAY,
        )

    def _preview_response(self, request, form):
        matching_counts, matched_rows = form.get_matching_summary(MAX_PREVIEW_ROWS_TO_DISPLAY)
        num_matched = matching_counts[ContactMatchingStatus.matched]

        template_filename = 'import_preview.html' if num_matched else 'import_no_matches.html'

        return self._template_response(
            request,
            f'admin/interaction/interaction/{template_filename}',
            PAGE_TITLE,
            num_matched=num_matched,
            num_unmatched=matching_counts[ContactMatchingStatus.unmatched],
            num_multiple_matches=matching_counts[ContactMatchingStatus.multiple_matches],
            matched_rows=matched_rows,
            num_matched_omitted=num_matched - len(matched_rows),
        )

    def _template_response(self, request, template, title, **extra_context):
        context = {
            **self.model_admin.admin_site.each_context(request),
            'opts': self.model_admin.model._meta,
            'title': title,
            **extra_context,
        }
        return TemplateResponse(request, template, context)


def _redirect_response(admin_view_name, **kwargs):
    import_errors_route_name = admin_urlname(Interaction._meta, admin_view_name)
    import_errors_url = reverse(import_errors_route_name, kwargs=kwargs)
    return HttpResponseRedirect(import_errors_url)
