from functools import partial

from django.contrib import admin
from django.urls import path
from reversion.admin import VersionAdmin

from datahub.company.models import Contact
from datahub.company.admin.merge_contact.step_1 import merge_select_other_contact
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
            *super().get_urls(),
        ]
