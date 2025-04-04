from django.db import transaction
from django.db.models.query_utils import Q
from django.db.models.signals import m2m_changed, post_delete, post_save
from reversion.models import Version

from datahub.company.models import Advisor
from datahub.interaction.models import Interaction
from datahub.investment.project.models import (
    InvestmentProject as DBInvestmentProject,
)
from datahub.investment.project.models import (
    InvestmentProjectTeamMember,
)
from datahub.search.deletion import delete_document
from datahub.search.investment import InvestmentSearchApp
from datahub.search.investment.models import InvestmentProject as SearchInvestmentProject
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async


def investment_project_sync_search(instance):
    """Sync investment project to the OpenSearch."""

    def sync_search_wrapper():
        if isinstance(instance, InvestmentProjectTeamMember):
            pk = instance.investment_project.pk
        else:
            pk = instance.pk

        sync_object_async(InvestmentSearchApp, pk)

    transaction.on_commit(sync_search_wrapper)


def remove_investment_project_from_opensearch(instance):
    """Remove task from es."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchInvestmentProject, pk),
    )


def investment_project_sync_search_interaction_change(instance):
    """Sync investment projects in OpenSearch when related interactions change.

    When an interaction changes, the OpenSearch index is also updated for
    the related investment project. The previous version also needs to be
    checked to make sure that if the investment project changes, the old
    investment project is also updated in the index.
    """
    pks = []

    if instance.investment_project is not None:
        pks.append(instance.investment_project.pk)

    previous_version = (
        Version.objects.get_for_object(
            instance,
        )
        .order_by('-revision__date_created')
        .first()
    )

    if previous_version is not None and 'investment_project_id' in previous_version.field_dict:
        pks.append(previous_version.field_dict['investment_project_id'])

    for pk in set([pk for pk in pks if pk is not None]):
        sync_object_async(InvestmentSearchApp, pk)


def investment_project_sync_search_adviser_change(instance):
    """post_save handler for advisers, to make sure that any projects they're linked to are
    resynced.

    This is primarily to update the teams stored against the project in OpenSearch.
    """

    def sync_search_wrapper():
        queryset = DBInvestmentProject.objects.filter(
            Q(created_by_id=instance.pk)
            | Q(client_relationship_manager_id=instance.pk)
            | Q(project_manager_id=instance.pk)
            | Q(project_assurance_adviser_id=instance.pk)
            | Q(team_members__adviser_id=instance.pk),
        )

        for project in queryset:
            sync_object_async(
                InvestmentSearchApp,
                project.pk,
            )

    transaction.on_commit(sync_search_wrapper)


def investment_project_sync_m2m_opensearch(instance, action, reverse, pk_set, **kwargs):
    """Sync opensearch when m2m fields change on the investment project."""
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return

    pks = pk_set if reverse else (instance.pk,)

    for pk in pks:
        sync_object_async(InvestmentSearchApp, pk)


investment_project_m2m_receivers = (
    SignalReceiver(
        m2m_changed,
        getattr(DBInvestmentProject, m2m_relation).through,
        investment_project_sync_m2m_opensearch,
        forward_kwargs=True,
    )
    for m2m_relation in [
        'business_activities',
        'competitor_countries',
        'uk_region_locations',
        'actual_uk_regions',
        'delivery_partners',
        'strategic_drivers',
    ]
)

receivers = (
    SignalReceiver(post_save, DBInvestmentProject, investment_project_sync_search),
    *investment_project_m2m_receivers,
    SignalReceiver(post_delete, DBInvestmentProject, remove_investment_project_from_opensearch),
    SignalReceiver(post_save, Interaction, investment_project_sync_search_interaction_change),
    SignalReceiver(post_delete, Interaction, investment_project_sync_search_interaction_change),
    SignalReceiver(post_save, InvestmentProjectTeamMember, investment_project_sync_search),
    SignalReceiver(post_delete, InvestmentProjectTeamMember, investment_project_sync_search),
    SignalReceiver(post_save, Advisor, investment_project_sync_search_adviser_change),
)
