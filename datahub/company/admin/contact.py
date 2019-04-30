from logging import getLogger
from typing import NamedTuple

import reversion
from django.contrib import admin, messages as django_messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from reversion.admin import VersionAdmin

from datahub.company.models import Contact
from datahub.core.admin import BaseModelAdminMixin
from datahub.core.admin_csv_import import BaseCSVImportForm
from datahub.search.signals import disable_search_signal_receivers


logger = getLogger(__name__)


class LoadEmailMarketingOptOutsForm(BaseCSVImportForm):
    """Form used for loading a CSV file to opt out contacts from email marketing."""

    csv_file_field_label = 'Email list (CSV file)'
    required_columns = {'email'}

    @reversion.create_revision()
    @disable_search_signal_receivers(Contact)
    def save(self, user):
        """Persists the data to the database."""
        reversion.set_user(user)
        reversion.set_comment('Loaded bulk email opt-out list.')

        with self.open_file_as_dict_reader() as dict_reader:
            return self._save(dict_reader, user)

    save.alters_data = True

    def _save(self, dict_reader, user):
        num_contacts_matched = 0
        num_contacts_updated = 0
        num_non_matching_email_addresses = 0

        for row in dict_reader:
            email = row['email'].strip()

            if not email:
                continue

            contacts = Contact.objects.filter(email__iexact=email)

            for contact in contacts:
                num_contacts_matched += 1

                if contact.accepts_dit_email_marketing:
                    num_contacts_updated += 1
                    contact.accepts_dit_email_marketing = False
                    contact.modified_by = user
                    contact.save()

            if not contacts:
                logger.warning(f'Could not find a contact with email address {email}')
                num_non_matching_email_addresses += 1

        return _ProcessOptOutResult(
            num_contacts_matched,
            num_contacts_updated,
            num_non_matching_email_addresses,
        )


class _ProcessOptOutResult(NamedTuple):
    num_contacts_matched: int
    num_contacts_updated: int
    num_non_matching_email_addresses: int

    @property
    def num_contacts_skipped(self):
        return self.num_contacts_matched - self.num_contacts_updated


@admin.register(Contact)
class ContactAdmin(BaseModelAdminMixin, VersionAdmin):
    """Contact admin."""

    search_fields = (
        'pk',
        'first_name',
        'last_name',
        'company__pk',
        'company__name',
    )
    raw_id_fields = (
        'company',
        'adviser',
        'archived_by',
    )
    readonly_fields = (
        'created',
        'modified',
        'archived_documents_url_path',
    )
    list_display = (
        'name',
        'company',
    )
    list_select_related = (
        'company',
    )
    exclude = (
        'created_on',
        'created_by',
        'modified_on',
        'modified_by',
    )

    def get_urls(self):
        """Gets the URLs for this model."""
        model_meta = self.model._meta
        return [
            *super().get_urls(),
            path(
                'load-email-marketing-opt-outs',
                self.admin_site.admin_view(self.opt_out_form),
                name=f'{model_meta.app_label}_{model_meta.model_name}'
                     f'_load-email-marketing-opt-outs',
            ),
        ]

    def opt_out_form(self, request, *args, **kwargs):
        """View containing a form to load email marketing opt outs."""
        if not self.has_change_permission(request):
            raise PermissionDenied

        if request.method != 'POST':
            return self._opt_out_form_response(request, LoadEmailMarketingOptOutsForm())

        form = LoadEmailMarketingOptOutsForm(request.POST, request.FILES)
        if not form.is_valid():
            return self._opt_out_form_response(request, form)

        opt_out_res = form.save(request.user)
        return self._opt_out_success_response(request, opt_out_res)

    def _opt_out_form_response(self, request, form):
        template_name = 'admin/company/contact/load_email_marketing_opt_outs.html'
        title = 'Load email marketing opt-outs'

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': title,
            'form': form,
        }
        return TemplateResponse(request, template_name, context)

    def _opt_out_success_response(self, request, opt_out_res):
        success_msg = (
            f'{opt_out_res.num_contacts_updated} contacts opted out of marketing emails '
            f'and {opt_out_res.num_contacts_skipped} contacts already opted out'
        )
        self.message_user(request, success_msg, django_messages.SUCCESS)

        if opt_out_res.num_non_matching_email_addresses:
            warning_msg = (
                f'{opt_out_res.num_non_matching_email_addresses} email addresses did not match a '
                f'contact'
            )
            self.message_user(request, warning_msg, django_messages.WARNING)

        changelist_url = reverse(admin_urlname(self.model._meta, 'changelist'))
        return HttpResponseRedirect(changelist_url)
