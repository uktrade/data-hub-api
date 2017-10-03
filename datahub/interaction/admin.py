from django.contrib import admin

from datahub.core.admin import BaseModelVersionAdmin
from .models import CommunicationChannel, Interaction, ServiceDelivery, ServiceOffer


@admin.register(CommunicationChannel)
class MetadataAdmin(admin.ModelAdmin):
    """Communication channel admin."""

    fields = ('name', )
    list_display = ('name', )
    readonly_fields = ('id',)
    search_fields = ('name', 'pk')


@admin.register(Interaction)
class InteractionAdmin(BaseModelVersionAdmin):
    """Interaction admin."""

    search_fields = (
        'id',
        'company__company_number',
        'company__company_name',
        'contact_email'
    )
    raw_id_fields = (
        'company',
        'dit_adviser',
        'investment_project',
        'contact',
        'created_by',
        'modified_by',
    )


@admin.register(ServiceDelivery)
class ServiceDeliveryAdmin(BaseModelVersionAdmin):
    """Service Delivery admin."""

    search_fields = (
        'id',
        'company__company_number',
        'company__company_name',
        'contact_email'
    )
    raw_id_fields = (
        'company',
        'dit_adviser',
        'contact',
        'event',
        'created_by',
        'modified_by',
    )


@admin.register(ServiceOffer)
class ServiceOfferAdmin(BaseModelVersionAdmin):
    """Service Offer admin."""

    raw_id_fields = ('event',)
