import logging

from datahub.company_activity.models import CompanyActivity, GreatExportEnquiry
from datahub.company_referral.models import CompanyReferral
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject
from datahub.investment_lead.models import EYBLead
from datahub.omis.order.models import Order


logger = logging.getLogger(__name__)


def relate_company_activity_to_interactions(batch_size=500):
    """
    Grabs all interactions so they can be related to the
    `CompanyActivity` model with bulk_create. Excludes any
    interactions already associated in the CompanyActivity model.

    Can be used to populate the CompanyActivity with missing interactions
    or to initially populate the model.
    """
    activity_interactions = set(CompanyActivity.objects.filter(
        interaction__isnull=False,
    ).values_list('interaction_id', flat=True))

    interactions = Interaction.objects.filter(
        company_id__isnull=False,
    ).values('id', 'date', 'company_id')

    objs = [
        CompanyActivity(
            interaction_id=interaction['id'],
            date=interaction['date'],
            company_id=interaction['company_id'],
            activity_source=CompanyActivity.ActivitySource.interaction,
        )
        for interaction in interactions
        if interaction['id'] not in activity_interactions
    ]

    bulk_create_activity(objs, batch_size)


def relate_company_activity_to_referrals(batch_size=500):
    """
    Grabs all referrals so they can be related to the
    `CompanyActivity` model with a bulk_create. Excludes any
    referrals already associated in the CompanyActivity model.

    Can be used to populate the CompanyActivity with missing referrals
    or to initially populate the model.
    """
    activity_referral = CompanyActivity.objects.filter(
        referral__isnull=False,
    ).values_list('referral_id', flat=True)

    referrals = CompanyReferral.objects.exclude(
        id__in=activity_referral,
    ).values('id', 'created_on', 'company_id')

    objs = [
        CompanyActivity(
            referral_id=referral['id'],
            date=referral['created_on'],
            company_id=referral['company_id'],
            activity_source=CompanyActivity.ActivitySource.referral,
        )
        for referral in referrals
    ]

    bulk_create_activity(objs, batch_size)


def relate_company_activity_to_investment_projects(batch_size=500):
    """
    Grabs all investment projects so they can be related to the
    `CompanyActivity` model with a bulk_create. Excludes any
    investment projects already associated in the CompanyActivity model.
    """
    activity_investments = set(
        CompanyActivity.objects.filter(
            investment__isnull=False,
        ).values_list('investment_id', flat=True),
    )

    investments = InvestmentProject.objects.filter(
        investor_company__isnull=False,
    ).values('id', 'created_on', 'investor_company_id')

    objs = [
        CompanyActivity(
            investment_id=investment['id'],
            date=investment['created_on'],
            company_id=investment['investor_company_id'],
            activity_source=CompanyActivity.ActivitySource.investment,
        )
        for investment in investments
        if investment['id'] not in activity_investments
    ]

    bulk_create_activity(objs, batch_size)


def relate_company_activity_to_orders(batch_size=500):
    """
    Grabs all omis orders so they can be related to the
    `CompanyActivity` model with a bulk_create. Excludes any
    order projects already associated in the CompanyActivity model.
    """
    activity_orders = set(
        CompanyActivity.objects.filter(
            order__isnull=False,
        ).values_list('order_id', flat=True),
    )

    orders = Order.objects.filter(
        company_id__isnull=False,
    ).values('id', 'created_on', 'company_id')

    objs = [
        CompanyActivity(
            order_id=order['id'],
            date=order['created_on'],
            company_id=order['company_id'],
            activity_source=CompanyActivity.ActivitySource.order,
        )
        for order in orders
        if order['id'] not in activity_orders
    ]

    bulk_create_activity(objs, batch_size)


def relate_company_activity_to_great(batch_size=500):
    """
    Grabs all great export enquiry so they can be related to the
    `CompanyActivity` model with a bulk_create. Excludes any
    great export enquiry already associated in the CompanyActivity model.
    """
    activity = set(
        CompanyActivity.objects.filter(
            great_export_enquiry_id__isnull=False,
        ).values_list('great_export_enquiry_id', flat=True),
    )

    great_export_enquiries = GreatExportEnquiry.objects.filter(
        company_id__isnull=False,
    ).values('id', 'created_on', 'company_id')

    objs = [
        CompanyActivity(
            great_export_enquiry_id=great_export_enquiry['id'],
            date=great_export_enquiry['created_on'],
            company_id=great_export_enquiry['company_id'],
            activity_source=CompanyActivity.ActivitySource.great_export_enquiry,
        )
        for great_export_enquiry in great_export_enquiries
        if great_export_enquiry['id'] not in activity
    ]

    bulk_create_activity(objs, batch_size)


def relate_company_activity_to_eyb_lead(batch_size=500):
    """
    Grabs all EYB leads so they can be related to the
    `CompanyActivity` model with a bulk_create. Excludes any
    EYB leads already associated in the CompanyActivity model.
    """
    activity = set(
        CompanyActivity.objects.filter(
            eyb_lead__isnull=False,
        ).values_list('eyb_lead', flat=True),
    )

    eyb_leads = EYBLead.objects.filter(
        company__isnull=False,
    ).values('id', 'created_on', 'company_id')

    objs = [
        CompanyActivity(
            eyb_lead_id=eyb_lead['id'],
            date=eyb_lead['created_on'],
            company_id=eyb_lead['company_id'],
            activity_source=CompanyActivity.ActivitySource.eyb_lead,
        )
        for eyb_lead in eyb_leads
        if eyb_lead['id'] not in activity
    ]

    bulk_create_activity(objs, batch_size)


def schedule_sync_data_to_company_activity(relate_function):
    """
    Schedules a task for the given function.
    """
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=relate_function,
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
    )
    logger.info(
        f'Task {job.id} {relate_function.__name__} scheduled.',
    )
    return job


def bulk_create_activity(objs, batch_size):
    total = len(objs)
    initial = 0

    while True:
        batch = objs[initial: initial + batch_size]
        if not batch:
            logger.info('Finished bulk creating CompanyActivities.')
            break
        logger.info(f'Creating in batches of: {batch_size} CompanyActivities. {total} remaining.')
        CompanyActivity.objects.bulk_create(objs=batch, batch_size=batch_size)
        total -= batch_size
        initial += batch_size
