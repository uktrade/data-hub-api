from django.contrib import admin

from reversion.admin import VersionAdmin

from .models import Interaction, ServiceDelivery, ServiceOffer


@admin.register(Interaction)
class InteractionAdmin(VersionAdmin):
    """Interaction admin."""

    search_fields = ['id', 'company__company_number', 'company__company_name', 'contact_email']
    raw_id_fields = ('company', 'dit_adviser', 'investment_project', 'contact')


@admin.register(ServiceDelivery)
class ServiceDeliveryAdmin(VersionAdmin):
    """Service Delivery admin."""

    search_fields = ['id', 'company__company_number', 'company__company_name', 'contact_email']
    raw_id_fields = ('company', 'dit_adviser', 'contact', 'event')


@admin.register(ServiceOffer)
class ServiceOfferAdmin(VersionAdmin):
    """Service Offer admin."""

    raw_id_fields = ('event',)
