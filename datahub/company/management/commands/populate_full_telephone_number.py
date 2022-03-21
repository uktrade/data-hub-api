from logging import getLogger

from django.core.management.base import BaseCommand
from django.db.models import F, Q, Value
from django.db.models.functions import Concat

from datahub.company.models.contact import Contact

logger = getLogger(__name__)


class Command(BaseCommand):
    """Command to delete investment projects."""

    def handle(self, *args, **options):
        """Populate full telephone number data."""
        logger.info('Populating full_telephone_number field...')

        Contact.objects.filter(
            Q(full_telephone_number='') | Q(full_telephone_number__isnull=True),
        ).update(
            full_telephone_number=Concat(
                F('telephone_countrycode'), Value(' '), F('telephone_number'),
            ),
        )

        logger.info('Finished populating full_telephone_number')
