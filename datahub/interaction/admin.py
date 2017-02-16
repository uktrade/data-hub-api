from django.contrib import admin

from reversion.admin import VersionAdmin

from .models import Interaction, ServiceDelivery


@admin.register(Interaction)
class InteractionAdmin(VersionAdmin):
    """Interaction admin."""

    search_fields = ['id', 'company__company_number', 'company__company_name', 'contact_email']


@admin.register(ServiceDelivery)
class ServiceDeliveryAdmin(VersionAdmin):
    """Service Delivery admin."""

    search_fields = ['id', 'company__company_number', 'company__company_name', 'contact_email']
