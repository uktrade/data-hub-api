from django.db.models import Prefetch

from datahub.company_activity.models import CompanyActivity as DBCompanyActivity
from datahub.interaction.models import InteractionDITParticipant
from datahub.search.apps import SearchApp
from datahub.search.company_activity.models import CompanyActivity


class CompanyActivitySearchApp(SearchApp):
    """SearchApp for company activity."""

    name = 'company-activity'
    search_model = CompanyActivity
    view_permissions = ('company_activity.view_companyactivity',)
    queryset = DBCompanyActivity.objects.select_related(
        'company',
        'interaction',
        'interaction__communication_channel',
        'interaction__service__parent',
        'referral',
        'referral__contact',
        'referral__created_by',
        'referral__recipient',
        'investment',
        'investment__investment_type',
        'investment__created_by',
        'order',
        'order__contact',
    ).prefetch_related(
        'interaction__contacts',
        Prefetch(
            'interaction__dit_participants',
            queryset=InteractionDITParticipant.objects.select_related('adviser', 'team'),
        ),)
