from celery import shared_task
from celery.utils.log import get_task_logger
from dateutil.relativedelta import relativedelta
from django.db.models import FilteredRelation, OuterRef, Q, Subquery
from django.utils import timezone
from django_pglocks import advisory_lock

from datahub.company.constants import AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG
from datahub.company.models.company import Company
from datahub.feature_flag.utils import is_feature_flag_active
from datahub.interaction.models import Interaction
from datahub.investment.project.models import InvestmentProject


logger = get_task_logger(__name__)


def _automatic_company_archive(limit, simulate):

    _8y_ago = timezone.now() - relativedelta(years=8)
    _3m_ago = timezone.now() - relativedelta(months=3)

    latest_interaction = Interaction.objects.filter(
        company=OuterRef('pk'),
    ).order_by('-date')

    companies_to_be_archived = Company.objects.annotate(
        latest_interaction_date=Subquery(
            latest_interaction.values('date')[:1],
        ),
        active_investment_projects=FilteredRelation(
            'investor_investment_projects',
            condition=Q(investor_investment_projects__status=InvestmentProject.Status.ONGOING),
        ),
    ).filter(
        Q(latest_interaction_date__date__lt=_8y_ago) | Q(latest_interaction_date__isnull=True),
        archived=False,
        duns_number__isnull=True,
        orders__isnull=True,
        investor_profiles__isnull=True,
        active_investment_projects__isnull=True,
        created_on__lt=_3m_ago,
        modified_on__lt=_3m_ago,
    )[:limit]

    for company in companies_to_be_archived:
        message = f'Automatically archived company: {company.id}'
        if simulate:
            logger.info(f'[SIMULATION] {message}')
            continue
        company.archived = True
        company.archived_reason = 'This record was automatically archived due to inactivity'
        company.archived_on = timezone.now()
        company.save(
            update_fields=[
                'archived',
                'archived_reason',
                'archived_on',
            ],
        )
        logger.info(message)


@shared_task(
    bind=True,
    acks_late=True,
    priority=9,
    max_retries=3,
    queue='long-running',
)
def automatic_company_archive(self, limit=1000, simulate=True):
    """
    Archive inactive companies.
    """
    if not is_feature_flag_active(AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG):
        logger.info(
            f'Feature flag "{AUTOMATIC_COMPANY_ARCHIVE_FEATURE_FLAG}" is not active, exiting.',
        )
        return

    with advisory_lock('automatic_company_archive', wait=False) as acquired:

        if not acquired:
            logger.info('Another instance of this task is already running.')
            return

        _automatic_company_archive(limit, simulate)
