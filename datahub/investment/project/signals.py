from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from datahub.investment.project.gva_utils import update_gross_value_added_for_investment_project
from datahub.investment.project.models import InvestmentProject, InvestmentProjectCode


@receiver(post_save, sender=InvestmentProject, dispatch_uid='project_code_project_post_save')
def project_code_project_post_save(sender, **kwargs):
    """Creates a project code for investment projects on creation.

    Projects with a CDMS project code do not get a new project code.

    This generates project codes for fixtures loaded via manage.py loaddata (i.e. when
    kwargs['raw'] is True), though that may need to change if fixed project codes are
    required for that fixtures.
    """
    instance = kwargs['instance']
    created = kwargs['created']
    if created and not instance.cdms_project_code:
        InvestmentProjectCode.objects.create(project=instance)


@receiver(
    pre_save,
    sender=InvestmentProject,
    dispatch_uid='update_gross_value_added_for_investment_project_pre_save',
)
def update_gross_value_added_for_investment_project_pre_save(sender, instance, **kwargs):
    """
    Checks the investment project and if anything has changed that could affect
    the Gross Value Added if required the values are updated.

    GVA can change if the sector, business activity is set to retail or the
    foreign equity investment is updated.
    """
    update_gross_value_added_for_investment_project(instance)
