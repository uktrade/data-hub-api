from django.contrib import admin

from datahub.core.admin import BaseModelVersionAdmin
from .models import Interaction, ServiceDelivery, ServiceOffer


@admin.register(Interaction)
class InteractionAdmin(BaseModelVersionAdmin):
    """Interaction admin."""

    search_fields = ['id', 'company__company_number', 'company__company_name', 'contact_email']
    raw_id_fields = ('company', 'dit_adviser', 'investment_project', 'contact')


@admin.register(ServiceDelivery)
class ServiceDeliveryAdmin(BaseModelVersionAdmin):
    """Service Delivery admin."""

    search_fields = ['id', 'company__company_number', 'company__company_name', 'contact_email']
    raw_id_fields = ('company', 'dit_adviser', 'contact', 'event')


@admin.register(ServiceOffer)
class ServiceOfferAdmin(BaseModelVersionAdmin):
    """Service Offer admin."""

    raw_id_fields = ('event',)
