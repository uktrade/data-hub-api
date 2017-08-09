from django.utils.module_loading import autodiscover_modules


def autodiscover():
    """Loads the `metadata` module in each individual apps."""
    autodiscover_modules('metadata')


default_app_config = 'datahub.metadata.apps.MetadataConfig'
