from logging import getLogger

from celery import shared_task

from datahub.investment.project.models import GVAMultiplier

logger = getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    queue='long-running',
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
            f'Unable to find GVA Multiplier [{gva_multiplier_id}]',
            f' - Unable to update associated investment projects',
        )
    else:
        investment_projects = instance.investment_projects.all()
        for investment_project in investment_projects.iterator():
            investment_project.save(update_fields=['gross_value_added'])
