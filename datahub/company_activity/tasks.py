import logging
from itertools import islice

from datahub.company_activity.models import CompanyActivity
from datahub.company_referral.models import CompanyReferral
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.interaction.models import Interaction


logger = logging.getLogger(__name__)


def schedule_sync_interactions_to_company_activity():
    """
    Schedules a task to relate all `Interaction`s to `CompanyActivity`s.

    Can be used to populate the CompanyActivity with missing interactions
    or to initially populate the model.
    """
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=relate_company_activity_to_interactions,
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
    )
    logger.info(
        f'Task {job.id} schedule_sync_interactions_to_company_activity scheduled.',
    )
    return job


def relate_company_activity_to_interactions(batch_size=500):
    """
    Grabs all interactions so they can be related to in the
    `CompanyActivity` model with bulk_create. Excludes any
    interactions already associated in the CompanyActivity model.

    Can be used to populate the CompanyActivity with missing interactions
    or to initially populate the model.
    """
    activity_interactions = CompanyActivity.objects.filter(
        interaction__isnull=False,
    ).values_list('interaction_id', flat=True)

    interactions = Interaction.objects.filter(
        company_id__isnull=False,
    ).values('id', 'date', 'company_id')

    objs = (
        CompanyActivity(
            interaction_id=interaction['id'],
            date=interaction['date'],
            company_id=interaction['company_id'],
            activity_source=CompanyActivity.ActivitySource.interaction,
        )
        for interaction in interactions
        if interaction['id'] not in activity_interactions
    )

    total = interactions.count()

    while True:
        batch = list(islice(objs, batch_size))
        if not batch:
            logger.info('Finished bulk creating CompanyActivities.')
            break
        logger.info(f'Bulk creating {batch_size} CompanyActivities, {total} remaining.')
        CompanyActivity.objects.bulk_create(objs=batch, batch_size=batch_size)
        total -= batch_size


def schedule_sync_referrals_to_company_activity():
    """
    Schedules a task to relate all `CompanyReferral`s to `CompanyActivity`s

    Can be used to populate the CompanyActivity with missing referrals
    or to initially populate the model.
    """
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=relate_company_activity_to_referrals,
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
    )
    logger.info(
        f'Task {job.id} schedule_sync_referrals_to_company_activity scheduled.',
    )
    return job


def relate_company_activity_to_referrals(batch_size=500):
    """
    Grabs all referrals so they can be related to in the
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

    objs = (
        CompanyActivity(
            referral_id=referral['id'],
            date=referral['created_on'],
            company_id=referral['company_id'],
            activity_source=CompanyActivity.ActivitySource.referral,
        )
        for referral in referrals
    )
    total = referrals.count()

    while True:
        batch = list(islice(objs, batch_size))
        if not batch:
            logger.info('Finished bulk creating CompanyActivities.')
            break
        logger.info(f'Bulk creating {batch_size} CompanyActivities, {total} remaining.')
        CompanyActivity.objects.bulk_create(objs=batch, batch_size=batch_size)
        total -= batch_size
