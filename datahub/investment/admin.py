"""Admin registration for investment models."""

from django.contrib import admin

from reversion.admin import VersionAdmin

from datahub.investment.models import (InvestmentProject)


@admin.register(InvestmentProject)
class InvestmentProjectAdmin(VersionAdmin):
    """Investment project admin."""

    search_fields = ['name']
    raw_id_fields = (
        'archived_by',
        'investor_company',
        'intermediate_company',
        'client_contacts',
        'client_relationship_manager',
        'referral_source_adviser',
        'project_manager',
        'project_assurance_adviser',
        'uk_company'
    )
