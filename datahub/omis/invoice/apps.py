from django.apps import AppConfig


class InvoiceConfig(AppConfig):
    """Django App Config for the Invoice app."""

    name = 'datahub.omis.invoice'
    label = 'omis_invoice'  # namespaced app. Use this e.g. when migrating
