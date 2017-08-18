from reversion.admin import VersionAdmin


class ConfigurableVersionAdmin(VersionAdmin):
    """
    Subclass of VersionAdmin that allows the excluded model fields for django-reversion
    to be easily set.

    This is in line with the example on:
    https://django-reversion.readthedocs.io/en/stable/admin.html#reversion-admin-versionadmin

    Excluded fields are not saved in django-reversion versions.

    This is set in the admin class because we're using django-reversion auto-registration
    via VersionAdmin.
    """

    reversion_excluded_fields = None

    def reversion_register(self, model, **options):
        """Used the the django-reversion model auto-registration mechanism."""
        if self.reversion_excluded_fields:
            options['exclude'] = self.reversion_excluded_fields
        super().reversion_register(model, **options)


class BaseModelVersionAdmin(ConfigurableVersionAdmin):
    """
    VersionAdmin subclass that excludes fields defined on BaseModel.

    These aren't particularly useful to save in django-reversion versions because
    created_by/created_on will not change between versions, and modified_on/modified_by
    is tracked by django-reversion separately in revisions.
    """

    reversion_excluded_fields = ('created_on', 'created_by', 'modified_on', 'modified_by')
