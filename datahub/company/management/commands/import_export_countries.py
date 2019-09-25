import codecs
import csv
from contextlib import closing, contextmanager
from logging import getLogger

import reversion
from django.core.management.base import BaseCommand
from django.db.models import Q

from datahub.company.models import Company, CompanyExportCountry
from datahub.documents.utils import get_s3_client_for_bucket
from datahub.metadata import models as metadata_models


logger = getLogger(__name__)


COMPANY_BATCH_SIZE = 1000


class InvalidImportDataError(Exception):
    """Error to raise if the import data doesn't pass validation"""

    pass


@contextmanager
def open_s3_file(bucket, key):
    """
    Open a file in s3 given the bucket and key.
    """
    s3_client = get_s3_client_for_bucket('default')
    response = s3_client.get_object(
        Bucket=bucket,
        Key=key,
    )['Body']
    with closing(response):
        yield codecs.getreader('utf-8')(response)


def import_from_csv(bucket, key):
    """
    Perform the import given an S3 bucket and key.

    We first validate the input file, ensuring that rows are sorted in order of
    company_id, and that all countries are valid.

    Next we rely on the function generate_company_countries to generate valid companies
    paired with lists of countries from the import file. For each generated pair,
    we just have to call company.set_external_source_export_countries.

    Finally we call update_missing_companies on the file, which is responsible for
    updating those companies that are missing from the file.
    """
    validate_input_file(bucket, key)

    for company, countries in generate_company_countries(bucket, key):
        with reversion.create_revision():
            company.set_external_source_export_countries(countries)

    # We separate this into another loop in order to keep the logic above simple
    update_missing_companies(bucket, key)


def validate_input_file(bucket, key):
    """
    Validate two things about the file:
    1. That rows are sorted by company id.
    2. That all of the country values are valid iso-alpha-2 codes
    present in the datahub db.
    """
    valid_country_codes = set(metadata_models.Country.objects.values_list(
        'iso_alpha2_code', flat=True,
    ))
    with open_s3_file(bucket, key) as csvfile:
        reader = csv.reader(csvfile)
        current_company_id = None
        for row in reader:
            [company_id, _, alpha_2] = row
            if not current_company_id:
                current_company_id = company_id
            elif company_id != current_company_id:
                if company_id < current_company_id:
                    raise InvalidImportDataError(
                        f'Data must be sorted by company id;'
                        f'{company_id} appeared after {current_company_id}',
                    )
                current_company_id = company_id
            if alpha_2 not in valid_country_codes:
                raise InvalidImportDataError(
                    f'{alpha_2} is not a valid country code',
                )


def generate_company_countries(bucket, key):
    """
    Generator which opens the given filename, and loops through it,
    yielding (company, countries) pairs.
    """
    with open_s3_file(bucket, key) as csvfile:
        reader = csv.reader(csvfile)

        countries = {
            c.iso_alpha2_code: c
            for c
            in metadata_models.Country.objects.all()
        }

        current_company = None
        current_countries = []
        for [row_company_id, _, row_alpha_2] in reader:
            if current_company and row_company_id != str(current_company.id):
                yield current_company, current_countries
                current_countries = []
                current_company = None
            if not current_company:
                try:
                    current_company = Company.objects.get(id=row_company_id)
                except Company.DoesNotExist:
                    continue
            current_countries.append(countries[row_alpha_2])
        if current_company:
            yield current_company, current_countries


def update_missing_companies(bucket, key):
    """
    Go through the input csv and update any companies that have are not present
    in the file and hence need to have all of their countries deleted.
    """
    # Our logic is absolutely reliant on the company ids being sorted.
    validate_input_file(bucket, key)
    assert COMPANY_BATCH_SIZE > 1
    with open_s3_file(bucket, key) as csvfile:
        reader = csv.reader(csvfile)
        try:
            first_company_id, _, _ = next(reader)
        except StopIteration:
            # Input file is empty, update them all!
            update_missing_companies_from_batch([], start=None, end=None)
            return

        # Delete any missing companies with id less than the first company id.
        update_missing_companies_from_batch([first_company_id], start=None, end=first_company_id)

        current_batch = [first_company_id]
        last_company_id = first_company_id
        for [company_id, _, _] in reader:
            last_company_id = company_id
            current_batch.append(company_id)
            if len(current_batch) == COMPANY_BATCH_SIZE:
                update_missing_companies_from_batch(
                    current_batch, start=current_batch[0], end=current_batch[-1],
                )
                current_batch = current_batch[-1:]

        if len(current_batch):
            update_missing_companies_from_batch(
                current_batch, start=current_batch[0], end=current_batch[-1],
            )

        update_missing_companies_from_batch(
            [last_company_id], start=last_company_id, end=None,
        )


def update_missing_companies_from_batch(id_batch, start=None, end=None):
    """
    Update the external source countries of interest for companies that
    are missing from a csv.
    For any companies with id in the range [start, end], where id
    is not present in id_batch, call company.set_external_source_export_countries([])
    """
    range_query = Q()
    if start:
        range_query &= Q(company_id__gte=start)
    if end:
        range_query &= Q(company_id__lte=end)
    missing_companies = Company.objects.filter(
        id__in=CompanyExportCountry.objects.filter(
            range_query,
            sources__contains=[CompanyExportCountry.SOURCES.external],
        ).exclude(
            company_id__in=id_batch,
        ).values('company_id'),
    ).prefetch_related(
        'unfiltered_export_countries',
        'unfiltered_export_countries__country',
    )
    for company in missing_companies:
        with reversion.create_revision():
            company.set_external_source_export_countries([])


class Command(BaseCommand):
    """Import Externally-sourced countries of interest command."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        parser.add_argument('bucket', help='S3 bucket where the CSV is stored.')
        parser.add_argument('object_key', help='S3 key of the CSV file.')

    def handle(self, *args, **options):
        """Handle the command"""
        import_from_csv(options['bucket'], options['object_key'])
