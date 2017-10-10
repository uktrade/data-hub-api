from django.apps import AppConfig


class PaymentConfig(AppConfig):
    """Django App Config for the Payment app."""

    name = 'datahub.omis.payment'
    label = 'omis-payment'  # namespaced app. Use this e.g. when migrating
