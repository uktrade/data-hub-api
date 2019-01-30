import json
from logging import getLogger

import mohawk
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from datahub.company.models.company import (
    Company,
)


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    Usage:
        ./manage.py import_from_activity_stream
    """

    def handle(self, *args, **options):
        """Fetches all verified companies from the activity stream and
        imports then, ensuring duplicates are not created
        """
        logger.info('Started')

        next_url = settings.ACTIVITY_STREAM_OUTGOING_URL
        query = json.dumps({
            'query': {
                'bool': {
                    'filter': [{
                        'term': {
                            'type': 'Create',
                        },
                    }, {
                        'term': {
                            'object.type': 'dit:directory:CompanyVerification',
                        },
                    }],
                },
            },
        }).encode('utf-8')
        content_type = 'application/json'

        credentials = {
            'id': settings.ACTIVITY_STREAM_OUTGOING_ACCESS_KEY_ID,
            'key': settings.ACTIVITY_STREAM_OUTGOING_SECRET_ACCESS_KEY,
            'algorithm': 'sha256',
        }

        while next_url:
            logger.info('Fetching page of companies: %s %s', next_url, query)

            # Fetch companies that should exist...
            auth_header = mohawk.Sender(
                credentials,
                next_url,
                'GET',
                content=query,
                content_type=content_type,
            ).request_header
            response_page = requests.get(next_url, headers={
                'Authorization': auth_header,
                'Content-Type': content_type,
            }, data=query).json()
            company_numbers_that_should_exist = set(
                item['object']['attributedTo']['dit:companiesHouseNumber']
                for item in response_page['orderedItems']
            )
            logger.info('Companies in page: %s', company_numbers_that_should_exist)

            with transaction.atomic():
                # ... find all those that already exist...
                company_numbers_that_do_exist = set(Company.objects.filter(
                    company_number__in=company_numbers_that_should_exist,
                ).values_list('company_number', flat=True))
                logger.info('Companies that already exist: %s', company_numbers_that_do_exist)

                # ... and create the difference
                company_numbers_to_create = \
                    company_numbers_that_should_exist - company_numbers_that_do_exist
                logger.info('Creating companies: %s', company_numbers_to_create)
                Company.objects.bulk_create([
                    Company(company_number=company_number)
                    for company_number in company_numbers_to_create
                ])
                logger.info('Companies created')

            next_url = response_page['next'] if 'next' in response_page else None
            query = b'{{}}'

        logger.info('Finished')
