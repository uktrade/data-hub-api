from functools import partial

from django.contrib import admin
from django.urls import path
from reversion.admin import VersionAdmin

from datahub.company.admin.merge.step_1 import merge_select_other_contact
from datahub.company.admin.merge.step_2 import select_primary_contact
from datahub.company.admin.merge.step_3 import confirm_merge_contacts
from datahub.company.models import Contact
from datahub.core.admin import BaseModelAdminMixin


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
        model_meta = self.model._meta

        return [
            path(
                'merge/step-1-select-other-contact',
                self.admin_site.admin_view(partial(merge_select_other_contact, self)),
                name=f'{model_meta.app_label}_'
                f'{model_meta.model_name}_merge-select-other-contact',
            ),
            path(
                'merge/step-2-select-primary-contact/',
                self.admin_site.admin_view(partial(select_primary_contact, self)),
                name=f'{model_meta.app_label}_'
                f'{model_meta.model_name}_merge-select-primary-contact',
            ),
            path(
                'merge/step-3-confirm/',
                self.admin_site.admin_view(partial(confirm_merge_contacts, self)),
                name=f'{model_meta.app_label}_' f'{model_meta.model_name}_merge-confirm',
            ),
            *super().get_urls(),
        ]
