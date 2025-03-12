import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.core.queues.job_scheduler import job_scheduler
from datahub.ingest.models import IngestedObject
from datahub.investment_lead.tasks.ingest_eyb_marketing import MARKETING_PREFIX
from datahub.investment_lead.tasks.ingest_eyb_triage import (
    eyb_triage_identification_task,
    TRIAGE_PREFIX,
)
from datahub.investment_lead.tasks.ingest_eyb_user import USER_PREFIX


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command to schedule the re-ingestion all records from the latest EYB objects.

    It does this by removing all EYB IngestedObject instances and then triggering the existing
    eyb_triage_identification_task that usually runs every hour. By removing the record of
    previously ingested files, the ingestion tasks assume all records contain unseen updates.

    Here, we only need to schedule the triage identification task as the rest are chained.
    """

    help = 'Schedules the re-ingestion of all records from the latest EYB objects'

    def handle(self, *args, **options):
        try:
            deleted = IngestedObject.objects.filter(
                Q(object_key__icontains=TRIAGE_PREFIX)
                | Q(object_key__icontains=USER_PREFIX)
                | Q(object_key__icontains=MARKETING_PREFIX),
            ).delete()
            logger.info(f'Deleted {deleted[0]} EYB IngestedObject instances')
            job_scheduler(
                function=eyb_triage_identification_task,
                description='Identify new EYB triage objects and schedule their ingestion',
            )
            logger.info('Scheduled re-ingestion of latest EYB objects')
        except Exception as e:
            logger.error(
                'An error occurred trying to schedule the re-ingestion of all records '
                f'from latest EYB objects: {str(e)}',
            )
