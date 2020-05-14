from logging import getLogger

from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.company.models import Company
from datahub.dnb_api.utils import (
    create_investigation,
    DNBServiceConnectionError,
    DNBServiceError,
    DNBServiceTimeoutError,
)

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to submit legacy dnb investigations to dnb-service.
    """

    help = (
        'Submit legacy dnb investigations to dnb-service. Investigations are '
        'submitted for companies where pending_dnb_investigation=True, '
        'investigation_id=False and website=None. This allows us to submit investigations '
        'for companies which only have a phone number for investigation evidence.'
    )

    def add_arguments(self, parser):
        """
        Parse arguments/options for this command.
        """
        parser.add_argument(
            '--simulate',
            help='Simulate investigation submissions.',
            action='store_true',
        )

    def handle(self, *args, **options):
        """
        Submit investigations matching criteria to dnb-service.
        """
        companies = Company.objects.filter(
            Q(website='') | Q(website=None),
            pending_dnb_investigation=True,
            dnb_investigation_id=None,
        ).order_by('created_on')
        for company in companies.iterator():
            if not (
                company.dnb_investigation_data
                and company.dnb_investigation_data.get('telephone_number')
            ):
                continue

            investigation_data = {
                'company_details': {
                    'primary_name': company.name,
                    'website': '',
                    'telephone_number': company.dnb_investigation_data['telephone_number'],
                    'address_line_1': company.address_1,
                    'address_line_2': company.address_2,
                    'address_town': company.address_town,
                    'address_county': company.address_county,
                    'address_postcode': company.address_postcode,
                    'address_country': company.address_country.iso_alpha2_code,
                },
            }
            message = f'Submitting investigation for company ID "{company.id}" to dnb-service.'
            if options['simulate']:
                logger.info(f'[SIMULATE] {message}')
                continue

            logger.info(message)

            # NOTE: there is some duplication here with
            # dnb_api/views.py::DNBCompanyInvestigationView however this command is temporary and
            # will be removed after use
            try:
                response = create_investigation(investigation_data)
            except (
                DNBServiceConnectionError,
                DNBServiceTimeoutError,
                DNBServiceError,
            ) as exc:
                logger.exception(str(exc))
                continue

            company.dnb_investigation_id = response['id']
            company.save(update_fields=['dnb_investigation_id'])
