from django.contrib import admin

from datahub.investment.project.proposition.models import Proposition


@admin.register(Proposition)
class PropositionAdmin(admin.ModelAdmin):
    """Proposition admin."""

    list_display = ('name', 'status', 'created_on')
    readonly_fields = ('id', 'created_by', 'modified_by')
    search_fields = ('=pk', 'name')
