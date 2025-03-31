import logging

from django.core.management.base import BaseCommand

from datahub.company.models import Company
from datahub.company_activity.models import GreatExportEnquiry
from datahub.metadata.models import Country

UNITED_KINGDOM = Country.objects.get(iso_alpha2_code='GB')


logger = logging.getLogger(__name__)


# TODO: Remove command once it has been run as one-off data modification


class Command(BaseCommand):
    """Command to do a one-off modification of GreatExportEnquiry companies without a country."""

    help = 'Sets address_country to UK for GreatExportEnquiry companies without a country.'

    def handle(self, *args, **options):
        """Sets address_country to UK for GreatExportEnquiry companies without a country."""
        try:
            enquiries_with_no_company_address_country = GreatExportEnquiry.objects.filter(
                company__address_country__isnull=True,
            )
            if enquiries_with_no_company_address_country.exists():
                logger.info(
                    f'Found {enquiries_with_no_company_address_country.count()}'
                    ' GreatExportEnquiry enquiries with no company address country. Modifying...',
                )
                companies_to_update = Company.objects.filter(
                    id__in=enquiries_with_no_company_address_country.values('company_id'),
                )
                logger.info(
                    f'Found {companies_to_update.count()} GreatExportEnquiry'
                    ' enquiring companies with no address country. Modifying...',
                )
                companies_to_update.update(address_country=UNITED_KINGDOM)
                logger.info('Finished modifying GreatExportEnquiry companies without a country.')
            else:
                logger.warning('No GreatExportEnquiry companies without a country. Exiting...')
        except Exception as e:
            logger.error(
                'An error occurred trying to modify GreatExportEnquiry'
                f' companies without a country: {str(e)}',
            )
