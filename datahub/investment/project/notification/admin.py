from django.contrib import admin

from datahub.core.admin import BaseModelAdminMixin
from datahub.investment.project.notification.models import InvestmentNotificationSubscription


@admin.register(InvestmentNotificationSubscription)
class InvestmentNotificationSubscriptionAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    """Investment Notification Subscription Admin."""

    search_fields = (
        'adviser__first_name', 'adviser__last_name', 'investment_project__name',
    )
    list_display = ('investment_project', 'adviser', 'estimated_land_date')
