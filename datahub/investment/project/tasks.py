from logging import getLogger

import reversion
from celery import shared_task
from django.db.models import Q

from datahub.core.constants import (
    InvestmentBusinessActivity as InvestmentBusinessActivityConstant,
    InvestmentType as InvestmentTypeConstant,
)
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.investment.project.models import GVAMultiplier, InvestmentProject

logger = getLogger(__name__)


def schedule_update_investment_projects_for_gva_multiplier_task(gva_multiplier_id):
    job = job_scheduler(
        queue_name=LONG_RUNNING_QUEUE,
        function=update_investment_projects_for_gva_multiplier_task,
        function_args=(gva_multiplier_id,),
        job_timeout=HALF_DAY_IN_SECONDS,
        max_retries=5,
        retry_backoff=True,
        retry_intervals=30,
    )
    logger.info(
        f'Task {job.id} update_investment_projects_for_gva_multiplier_task',
    )
    return job


# @shared_task(
#     autoretry_for=(Exception,),
#     queue='long-running',
#     max_retries=5,
#     retry_backoff=30,
# )
def update_investment_projects_for_gva_multiplier_task(gva_multiplier_id):
    """
    Updates the normalised gross_value_added for all investment projects
    with the associated GVA Multiplier.
    """
    try:
        instance = GVAMultiplier.objects.get(id=gva_multiplier_id)
    except GVAMultiplier.DoesNotExist:
        logger.warning(
            f'Unable to find GVA Multiplier [{gva_multiplier_id}]'
            ' - Unable to update associated investment projects',
        )
    else:
        _update_investment_projects_for_gva_multiplier(instance)


def _update_investment_projects_for_gva_multiplier(gva_multiplier):
    """
    Update gross_value_added for a GVA Multipliers related investment projects.

    Saving the projects updates the gross_value_added via pre_save signal.
    """
    investment_projects = gva_multiplier.investment_projects.all()
    for investment_project in investment_projects.iterator():
        investment_project.save(update_fields=['gross_value_added'])


@shared_task(
    queue='long-running',
)
def refresh_gross_value_added_value_for_fdi_investment_projects():
    """
    Loops over all investment projects that GVA
    could be calculated for and saving the project.

    Saving the project in turn calls the pre_save method
    'update_gross_value_added_for_investment_project_pre_save'
    which sets the Gross Value added data for a project.
    """
    investment_projects = get_investment_projects_to_refresh_gva_values()
    for project in investment_projects.iterator():
        project.save(update_fields=['gross_value_added', 'gva_multiplier'])


def get_investment_projects_to_refresh_gva_values():
    """Get investment projects. returns: All projects that GVA can be calculated for."""
    return InvestmentProject.objects.filter(
        investment_type_id=InvestmentTypeConstant.fdi.value.id,
    ).filter(
        Q(
            sector__isnull=False,
        ) | Q(
            business_activities__in=[
                InvestmentBusinessActivityConstant.retail.value.id,
                InvestmentBusinessActivityConstant.sales.value.id,
            ],
        ),
    )


def get_investment_projects_for_country_of_origin_update():
    """
    Get investment projects that do not have set country of origin and have
    investor company assigned.
    """
    return InvestmentProject.objects.select_related(
        'investor_company__address_country',
    ).filter(
        country_investment_originates_from__isnull=True,
        investor_company__isnull=False,
    )


@shared_task(
    queue='long-running',
)
def update_country_of_origin_for_investment_projects():
    """
    Loops over all investment projects that do not have country of origin updated and
    copy address country value from the corresponding investor company.
    """
    investment_projects = get_investment_projects_for_country_of_origin_update()
    for project in investment_projects.iterator():
        with reversion.create_revision():
            project.country_investment_originates_from = project.investor_company.address_country
            project.save(update_fields=['country_investment_originates_from'])

            reversion.set_comment('Automated country of origin update.')
