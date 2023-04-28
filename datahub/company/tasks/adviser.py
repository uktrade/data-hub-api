import logging

from datetime import date

import reversion

from dateutil.relativedelta import relativedelta

from django.db.models import Exists, OuterRef, Q
from django_pglocks import advisory_lock

from datahub.company.models import Advisor, Company, Contact, OneListCoreTeamMember
from datahub.company_referral.models import CompanyReferral
from datahub.core.queues.constants import HALF_DAY_IN_SECONDS
from datahub.core.queues.job_scheduler import job_scheduler
from datahub.core.queues.scheduler import LONG_RUNNING_QUEUE
from datahub.core.realtime_messaging import send_realtime_message
from datahub.event.models import Event
from datahub.interaction.models import Interaction
from datahub.investment.opportunity.models import LargeCapitalOpportunity
from datahub.investment.project.models import InvestmentProject, InvestmentProjectTeamMember
from datahub.omis.order.models import Order


logger = logging.getLogger(__name__)


def _automatic_adviser_deactivate(limit=1000, simulate=False):
    two_years_ago = date.today() - relativedelta(years=2)
    advisers_to_be_deactivated = Advisor.objects.filter(
        ~Exists(Interaction.objects.filter(
            (
                Q(date__gte=two_years_ago)
                | Q(modified_on__gte=two_years_ago)
            )
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(archived_by_id=OuterRef('pk'))
                | Q(dit_participants__adviser_id=OuterRef('pk'))
            ),
        )),
        ~Exists(CompanyReferral.objects.filter(
            Q(modified_on__gte=two_years_ago)
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(completed_by_id=OuterRef('pk'))
            ),
        )),
        ~Exists(Company.objects.filter(
            Q(modified_on__gte=two_years_ago)
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(archived_by_id=OuterRef('pk'))
                | Q(one_list_account_owner_id=OuterRef('pk'))
                | Q(transferred_by_id=OuterRef('pk'))
            ),
        )),
        ~Exists(Contact.objects.filter(
            Q(modified_on__gte=two_years_ago)
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(archived_by_id=OuterRef('pk'))
                | Q(adviser_id=OuterRef('pk'))
            ),
        )),
        ~Exists(Order.objects.filter(
            (
                Q(modified_on__gte=two_years_ago)
                | Q(paid_on__gte=two_years_ago)
                | Q(completed_on__gte=two_years_ago)
                | Q(cancelled_on__gte=two_years_ago)
            )
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(completed_by_id=OuterRef('pk'))
                | Q(cancelled_by_id=OuterRef('pk'))
                | Q(assignees__adviser_id=OuterRef('pk'))
                | Q(subscribers__adviser_id=OuterRef('pk'))
            ),
        )),
        ~Exists(LargeCapitalOpportunity.objects.filter(
            Q(modified_on__gte=two_years_ago)
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
            ),
        )),
        ~Exists(InvestmentProject.objects.filter(
            Q(modified_on__gte=two_years_ago)
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(archived_by_id=OuterRef('pk'))
                | Q(client_relationship_manager_id=OuterRef('pk'))
                | Q(project_manager_id=OuterRef('pk'))
                | Q(project_manager_first_assigned_by_id=OuterRef('pk'))
                | Q(referral_source_adviser_id=OuterRef('pk'))
                | Q(project_assurance_adviser_id=OuterRef('pk'))
            ),
        )),
        ~Exists(Event.objects.filter(
            (
                Q(modified_on__gte=two_years_ago)
                | Q(start_date__gte=two_years_ago)
                | Q(end_date__gte=two_years_ago)
            )
            & (
                Q(created_by_id=OuterRef('pk'))
                | Q(modified_by_id=OuterRef('pk'))
                | Q(organiser_id=OuterRef('pk'))
            ),
        )),
        ~Exists(OneListCoreTeamMember.objects.filter(
            (Q(adviser_id=OuterRef('pk'))),
        )),
        ~Exists(InvestmentProjectTeamMember.objects.filter(
            (Q(adviser_id=OuterRef('pk'))),
        )),
        date_joined__lt=two_years_ago,
        is_active=True,
        sso_email_user_id__isnull=True,
    )[:limit]

    for adviser in advisers_to_be_deactivated:
        with reversion.create_revision():
            message = f'Automatically de-activate adviser: {adviser.id}'
            if simulate:
                logger.info(f'[SIMULATION] {message}')
                continue
            adviser.is_active = False
            adviser.save(update_fields=['is_active'])
            logger.info(message)
            reversion.set_comment('Automated deactivated adviser.')

    return advisers_to_be_deactivated.count()


def schedule_automatic_adviser_deactivate(limit=1000, simulate=False):
    job = job_scheduler(
        function=automatic_adviser_deactivate,
        function_args=(
            limit,
            simulate,
        ),
        max_retries=3,
        queue_name=LONG_RUNNING_QUEUE,
        job_timeout=HALF_DAY_IN_SECONDS,
    )
    logger.info(
        f'Task {job.id} automatic_adviser_deactivate',
    )
    return job


def automatic_adviser_deactivate(limit=1000, simulate=False):
    """
    Deactivate inactive advisers.
    """
    with advisory_lock('automatic_adviser_deactivate', wait=False) as acquired:

        if not acquired:
            logger.info('Another instance of this task is already running.')
            return

        deactivated_count = _automatic_adviser_deactivate(limit=limit, simulate=simulate)
        realtime_message = (
            f'datahub.company.tasks.automatic_adviser_deactivate deactivated: {deactivated_count}'
        )
        if simulate:
            realtime_message = f'[SIMULATE] {realtime_message}'
        send_realtime_message(realtime_message)
