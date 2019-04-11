from logging import getLogger

from celery import shared_task

from datahub.investment.project.models import GVAMultiplier

logger = getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
    max_retries=5,
    retry_backoff=30,
)
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
