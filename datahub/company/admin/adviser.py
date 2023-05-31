from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from reversion.admin import VersionAdmin

from datahub.company.admin.adviser_forms import AddAdviserFromSSOForm
from datahub.company.models import Advisor


@admin.register(Advisor)
class AdviserAdmin(VersionAdmin, UserAdmin):
    """Adviser admin."""

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'email',
                    'sso_email_user_id',
                    'sso_user_id',
                    'password',
                ),
            },
        ),
        (
            'PERSONAL INFO',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'contact_email',
                    'telephone_number',
                    'dit_team',
                ),
            },
        ),
        (
            'PERMISSIONS',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (
            'IMPORTANT DATES',
            {
                'fields': (
                    'last_login',
                    'date_joined',
                ),
            },
        ),
        (
            'OTHER',
            {
                'fields': (
                    'feature_groups',
                    'features_info',
                    'features',
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2'),
            },
        ),
    )
    list_display = ('email', 'first_name', 'last_name', 'dit_team', 'is_active', 'is_staff')
    readonly_fields = ('features_info',)
    search_fields = (
        '=pk',
        'first_name',
        'last_name',
        'email',
        'sso_email_user_id',
        'sso_user_id',
        '=dit_team__pk',
        'dit_team__name',
    )
    filter_horizontal = ('feature_groups', 'features')
    ordering = ('email',)

    def features_info(self, obj):
        """
        Shows if any individual user feature flag already exists in user feature flag group
        assigned to the adviser.
        """
        info = []
        features = set(obj.features.values_list('code', flat=True))

        for feature in obj.feature_groups.all():
            grouped = feature.features.values_list('code', flat=True)
            common = features.intersection(grouped)
            if len(common):
                info.append(
                    f'"{feature.code}" feature group already contains following'
                    f' feature flags: {", ".join(sorted(common))}',
                )
        if len(info) == 0:
            info = ['No problems detected.']
        return '\n'.join(info)

    def get_urls(self):
        """
        Gets the admin URLs for this model.

        This adds an additional route for the add adviser from SSO view.
        """
        model_opts = self.model._meta

        add_sso_user_admin = AddAdviserFromSSOAdmin(self.model, self.admin_site)

        return [
            path(
                'add-from-sso/',
                self.admin_site.admin_view(add_sso_user_admin.add_view),
                name=f'{model_opts.app_label}_'
                     f'{model_opts.model_name}_add-from-sso',
            ),
            *super().get_urls(),
        ]


class AddAdviserFromSSOAdmin(AdviserAdmin):
    """
    Variant of AdviserAdmin with a different add form.

    This is used as part of simple workaround to enable us to have two different
    add adviser forms without reimplementing the entire view.

    This version of the add adviser form fetches user details from Staff SSO.
    """

    add_form_template = 'admin/company/advisor/add_from_sso.html'
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('search_email',),
        }),
    )
    add_form = AddAdviserFromSSOForm
