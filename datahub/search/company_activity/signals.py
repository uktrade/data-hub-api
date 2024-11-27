from django.db import transaction
from django.db.models.signals import post_delete, post_save

from datahub.company.models import (
    Company as DBCompany,
)
from datahub.company_activity.models import CompanyActivity as DBCompanyActivity
from datahub.company_activity.models import GreatExportEnquiry as DBGreatExportEnquiry
from datahub.company_referral.models import CompanyReferral as DBCompanyReferral
from datahub.interaction.models import (
    Interaction as DBInteraction,
)
from datahub.investment.project.models import InvestmentProject as DBInvestmentProject
from datahub.investment_lead.models import EYBLead as DBEYBLead
from datahub.omis.order.models import Order as DBOrder
from datahub.search.company_activity import CompanyActivitySearchApp
from datahub.search.company_activity.models import (
    CompanyActivity as SearchCompanyActivity,
)
from datahub.search.deletion import delete_document
from datahub.search.signals import SignalReceiver
from datahub.search.sync_object import sync_object_async, sync_related_objects_async


def sync_activity_to_opensearch(instance):
    """Sync activity to the OpenSearch."""
    transaction.on_commit(
        lambda: sync_object_async(CompanyActivitySearchApp, instance.pk),
    )


def sync_related_activities_to_opensearch(instance):
    """Sync related activities objects to DB such as interactions, referalls etc."""
    transaction.on_commit(
        lambda: sync_related_objects_async(
            instance, 'activities', None, 'company-activity',
        ),
    )


def sync_related_activity_to_opensearch(instance):
    """Sync related activities objects to DB such as interactions, referalls etc."""
    transaction.on_commit(
        lambda: sync_related_objects_async(
            instance, 'activity', None, 'company-activity',
        ),
    )


def remove_interaction_from_opensearch(instance):
    """Remove company activity from opensearch."""
    transaction.on_commit(
        lambda pk=instance.pk: delete_document(SearchCompanyActivity, pk),
    )


receivers = (
    SignalReceiver(post_save, DBCompanyActivity, sync_activity_to_opensearch),
    SignalReceiver(post_save, DBCompany, sync_related_activities_to_opensearch),
    SignalReceiver(post_save, DBInteraction, sync_related_activity_to_opensearch),
    SignalReceiver(post_save, DBCompanyReferral, sync_related_activity_to_opensearch),
    SignalReceiver(post_save, DBOrder, sync_related_activity_to_opensearch),
    SignalReceiver(post_save, DBGreatExportEnquiry, sync_related_activity_to_opensearch),
    SignalReceiver(post_save, DBInvestmentProject, sync_related_activity_to_opensearch),
    SignalReceiver(post_save, DBEYBLead, sync_related_activity_to_opensearch),
    SignalReceiver(post_delete, DBCompanyActivity, remove_interaction_from_opensearch),
)
