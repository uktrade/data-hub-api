from django.contrib import admin

from .models import Order, OrderAssignee, OrderSubscriber


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for orders."""

    search_fields = ('reference',)
    readonly_fields = (
        'id',
        'net_cost',
        'subtotal_cost',
        'vat_cost',
        'total_cost',
    )
    raw_id_fields = (
        'created_by',
        'modified_by',
        'company',
        'contact',
        'quote',
        'invoice',
        'sector',
    )


@admin.register(OrderSubscriber)
class OrderSubscriberAdmin(admin.ModelAdmin):
    """Admin for order subscribers."""

    raw_id_fields = (
        'created_by',
        'modified_by',
        'order',
        'adviser',
    )


@admin.register(OrderAssignee)
class OrderAssigneeAdmin(admin.ModelAdmin):
    """Admin for order assignees."""

    raw_id_fields = (
        'created_by',
        'modified_by',
        'order',
        'adviser',
        'team',
    )
