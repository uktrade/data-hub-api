from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver

from datahub.investment.project.gva_utils import set_gross_value_added_for_investment_project
from datahub.investment.project.models import (
    GVAMultiplier,
    InvestmentProject,
    InvestmentProjectCode,
)
from datahub.investment.project.tasks import update_investment_projects_for_gva_multiplier_task


@receiver(
    post_save,
    sender=InvestmentProject,
    dispatch_uid='project_code_project_post_save',
)
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
    dispatch_uid='set_gross_value_added_for_investment_project_pre_save',
)
def set_gross_value_added_for_investment_project_pre_save(sender, instance, **kwargs):
    """
    Checks the investment project and if anything has changed that could affect
    the Gross Value Added if required the values are updated.

    GVA can change if the sector, business activity is set to retail or the
    foreign equity investment is updated.

    However, business activities are a many-to-many field and so can be updated without
    triggering this signal. There is a separate signal receiver below to reliably
    pick up changes to them.
    """
    set_gross_value_added_for_investment_project(instance)


@receiver(
    m2m_changed,
    sender=InvestmentProject.business_activities.through,
    dispatch_uid='update_gross_value_added_on_project_business_activities_m2m_changed',
)
def update_gross_value_added_on_project_business_activities_m2m_changed(
    sender,
    instance,
    **kwargs,
):
    """Update the project's gross value added value when its business activities change."""
    if kwargs['action'] in ('post_add', 'post_remove', 'post_clear') and not kwargs['reverse']:
        # Note: we are not in the middle of a call to .save() on the project here
        # To avoid a double-save, we simply call save on the instance which will trigger the
        # pre_save signal
        instance.save(
            update_fields=('gross_value_added', 'gva_multiplier'),
        )


@receiver(
    post_save,
    sender=GVAMultiplier,
    dispatch_uid='update_update_investment_projects_for_gva_multiplier_post_save',
)
def update_investment_projects_for_gva_multiplier_post_save(sender, **kwargs):
    """
    Calls a task to update the normalised gross_value_added for all investment projects
    with the associated GVA Multiplier.

    If the GVA Multiplier is being created no need to call the task as the GVA Multiplier
    won't have any investment projects associated with it.
    """
    instance = kwargs['instance']
    created = kwargs['created']
    if not created:
        update_investment_projects_for_gva_multiplier_task.apply_async(
            args=(instance.pk,),
        )
