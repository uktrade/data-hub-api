from django.contrib import admin
from django.utils.html import format_html
from rest_framework.reverse import reverse

from datahub.investment.report.models import SPIReport


@admin.register(SPIReport)
class SPIReportAdmin(admin.ModelAdmin):
    """SPI Report admin."""

    fields = ('id', 'created_on')
    readonly_fields = fields

    list_display = (
        'created_on', 'report',
    )
    list_filter = (
        'created_on',
    )
    date_hierarchy = 'created_on'

    def report(self, instance):
        """URL to the report download."""
        href = reverse(
            'investment-report:download-spi-report',
            kwargs={
                'pk': instance.pk,
            },
        )
        return format_html(
            '<a href="{href}">Click to download.</a>',
            href=href,
        )

    def has_add_permission(self, request):
        """Disallow adding new report."""
        return False
