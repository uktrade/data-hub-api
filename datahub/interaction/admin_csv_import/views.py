import io
from datetime import timedelta
from itertools import islice

from django.conf import settings
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.auth.decorators import permission_required
from django.contrib.messages import ERROR
from django.http import FileResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from datahub.company.contact_matching import ContactMatchingStatus
from datahub.core.admin import max_upload_size
from datahub.core.csv import CSV_CONTENT_TYPE
from datahub.core.exceptions import DataHubException
from datahub.interaction.admin_csv_import.cache_utils import (
    CACHE_VALUE_TIMEOUT,
    load_result_counts_by_status,
    load_unmatched_rows_csv_contents,
    save_result_counts_by_status,
    save_unmatched_rows_csv_contents,
)
from datahub.interaction.admin_csv_import.file_form import InteractionCSVForm
from datahub.interaction.models import Interaction, InteractionPermission

MAX_ERRORS_TO_DISPLAY = 50
MAX_PREVIEW_ROWS_TO_DISPLAY = 100
PAGE_TITLE = gettext_lazy('Import interactions')

INVALID_TOKEN_MESSAGE_DURING_SAVE = gettext_lazy(
    'The CSV file referenced is no longer available and may have expired. Please upload '
    'the file again.',
)
INVALID_TOKEN_MESSAGE_POST_SAVE = gettext_lazy(
    'Sorry, we could not find the results for that import operation. They may have expired.',
)


interaction_change_all_permission_required = method_decorator(
    permission_required(
        f'interaction.{InteractionPermission.change_all}',
        raise_exception=True,
    ),
)


class InteractionCSVImportAdmin:
    """Views related to importing interactions from a CSV file."""

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
            path(
                'import/<token>/save',
                admin_site.admin_view(self.save),
                name=f'{model_meta.app_label}_{model_meta.model_name}_import-save',
            ),
            path(
                'import/<token>/results',
                admin_site.admin_view(self.complete),
                name=f'{model_meta.app_label}_{model_meta.model_name}_import-complete',
            ),
            path(
                'import/<token>/download-unmatched',
                admin_site.admin_view(self.download_unmatched),
                name=f'{model_meta.app_label}_{model_meta.model_name}_import-download-unmatched',
            ),
        ]

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
            return self._error_list_response(request, form)

        return self._preview_response(request, form)

    @interaction_change_all_permission_required
    @method_decorator(require_POST)
    def save(self, request, token=None, *args, **kwargs):
        """Create interactions from a CSV file that was loaded in the select_file view."""
        form = InteractionCSVForm.from_token(token)

        if not form:
            self.model_admin.message_user(request, INVALID_TOKEN_MESSAGE_DURING_SAVE, ERROR)
            return _redirect_response('changelist')

        if not form.is_valid():
            # This should not happen, so we simply raise an error to alert us if it does
            raise DataHubException('Unexpected form re-validation failure')

        matching_counts, unmatched_row_collector = form.save(request.user)
        save_result_counts_by_status(token, matching_counts)

        unmatched_rows_csv_contents = unmatched_row_collector.to_raw_csv()
        if unmatched_rows_csv_contents:
            save_unmatched_rows_csv_contents(token, unmatched_rows_csv_contents)

        # Redirect to another page to display a confirmation message on success (following the
        # standard Django pattern to limit the possibility of a form resubmission on page
        # refresh).
        # For consistency, the required state is kept in the cache.
        return _redirect_response('import-complete', token=token)

    @interaction_change_all_permission_required
    def complete(self, request, token=None, *args, **kwargs):
        """Display a confirmation page following a successful import operation."""
        counts_by_status = load_result_counts_by_status(token)

        if not counts_by_status:
            self.model_admin.message_user(request, INVALID_TOKEN_MESSAGE_POST_SAVE, ERROR)
            return _redirect_response('changelist')

        return self._complete_response(request, token, counts_by_status)

    @interaction_change_all_permission_required
    def download_unmatched(self, request, token=None, *args, **kwargs):
        """Download unmatched rows as a CSV file following a successful import operation."""
        unmatched_rows_csv_contents = load_unmatched_rows_csv_contents(token)

        if not unmatched_rows_csv_contents:
            self.model_admin.message_user(request, INVALID_TOKEN_MESSAGE_POST_SAVE, ERROR)
            return _redirect_response('changelist')

        timestamp = now().strftime('%Y-%m-%d-%H-%M-%S')
        filename = f'Unmatched interactions - {timestamp}.csv'

        return FileResponse(
            io.BytesIO(unmatched_rows_csv_contents),
            as_attachment=True,
            content_type=CSV_CONTENT_TYPE,
            filename=filename,
        )

    def _select_file_form_response(self, request, form):
        return self._template_response(
            request,
            'admin/interaction/interaction/import_select_file.html',
            PAGE_TITLE,
            form=form,
        )

    def _error_list_response(self, request, form):
        errors = form.get_row_error_iterator()
        limited_errors = list(islice(errors, MAX_ERRORS_TO_DISPLAY))
        num_errors_omitted = sum(1 for _ in errors)

        return self._template_response(
            request,
            'admin/interaction/interaction/import_row_errors.html',
            PAGE_TITLE,
            errors=limited_errors,
            num_errors_omitted=num_errors_omitted,
            max_errors=MAX_ERRORS_TO_DISPLAY,
        )

    def _preview_response(self, request, form):
        token = form.save_to_cache()
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
            token=token,
        )

    def _complete_response(self, request, token, counts_by_status):
        return self._template_response(
            request,
            f'admin/interaction/interaction/import_complete.html',
            PAGE_TITLE,
            token=token,
            download_timeout_mins=CACHE_VALUE_TIMEOUT // timedelta(minutes=1),
            num_matched=counts_by_status[ContactMatchingStatus.matched],
            num_unmatched=counts_by_status[ContactMatchingStatus.unmatched],
            num_multiple_matches=counts_by_status[ContactMatchingStatus.multiple_matches],
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
