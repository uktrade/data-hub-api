"""Various services."""
import csv
import io
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime
from logging import getLogger
from urllib.parse import urlparse

import requests
import sentry_sdk
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries, transaction
from lxml import etree

from datahub.company.ch_constants import (
    COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING,
    CSV_FIELD_NAMES,
    CSV_RELEVANT_FIELDS,
)
from datahub.core import constants
from datahub.core.utils import slice_iterable_into_chunks, stream_to_file_pointer

logger = getLogger(__name__)


UPSERT_SQL_STATEMENT = """
INSERT INTO company_companieshousecompany (
    company_number,
    company_category,
    company_status,
    incorporation_date,
    "name",
    registered_address_1,
    registered_address_2,
    registered_address_country_id,
    registered_address_county,
    registered_address_postcode,
    registered_address_town,
    sic_code_1,
    sic_code_2,
    sic_code_3,
    sic_code_4,
    uri
) VALUES (
    %(company_number)s,
    %(company_category)s,
    %(company_status)s,
    %(incorporation_date)s,
    %(name)s,
    %(registered_address_1)s,
    %(registered_address_2)s,
    %(registered_address_country_id)s,
    %(registered_address_county)s,
    %(registered_address_postcode)s,
    %(registered_address_town)s,
    %(sic_code_1)s,
    %(sic_code_2)s,
    %(sic_code_3)s,
    %(sic_code_4)s,
    %(uri)s
  )
ON CONFLICT (company_number)
DO UPDATE SET (
    company_category,
    company_status,
    incorporation_date,
    "name",
    registered_address_1,
    registered_address_2,
    registered_address_country_id,
    registered_address_county,
    registered_address_postcode,
    registered_address_town,
    sic_code_1,
    sic_code_2,
    sic_code_3,
    sic_code_4,
    uri
) = (
    %(company_category)s,
    %(company_status)s,
    %(incorporation_date)s,
    %(name)s,
    %(registered_address_1)s,
    %(registered_address_2)s,
    %(registered_address_country_id)s,
    %(registered_address_county)s,
    %(registered_address_postcode)s,
    %(registered_address_town)s,
    %(sic_code_1)s,
    %(sic_code_2)s,
    %(sic_code_3)s,
    %(sic_code_4)s,
    %(uri)s
)
"""


def is_relevant_company_type(row):
    """
    Returns whether the company is of a relevant type (and should be loaded to our database).

    This is used to filter out companies that are not relevant for how we use Companies House
    data, such as foreign companies or companies where Companies House does not maintain address
    records.

    This is done using the CompanyCategory column in the source data, as this proved to be the
    most reliable way. (The prefix used in the company number also gives useful information about
    the type of company, but this is not used here. RegAddress.Country and CountryOfOrigin are
    not entirely reliable for detecting foreign companies.)
    """
    lower_company_category = row['company_category'].lower()
    if lower_company_category not in COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING:
        message = (f'Unknown Companies House company category {row["company_category"]} '
                   f'encountered. Update the company category to business type mapping to '
                   f'indicate if it should be loaded.')
        logger.warning(message)
        sentry_sdk.capture_message(message)
    return bool(COMPANY_CATEGORY_TO_BUSINESS_TYPE_MAPPING.get(lower_company_category))


def get_ch_latest_dump_file_list(url, selector='.omega a'):
    """Fetch a list of last published basic data dumps from CH, using a given selector."""
    response = requests.get(url)
    parser = etree.HTMLParser()
    root = etree.parse(io.BytesIO(response.content), parser).getroot()

    url_base = urlparse(url)

    result = []
    for anchor in root.cssselect(selector):
        href = anchor.attrib['href']
        # Fix broken url
        if 'AsOneFile' not in href:
            result.append(f'{url_base.scheme}://{url_base.hostname}/{href}')
    return result


def transform_ch_row(row):
    """Filter out the irrelevant fields from a CH data row and normalize the data."""
    ret = {}
    for name in CSV_RELEVANT_FIELDS:
        ret[name] = row.get(name, '')

    if ret['registered_address_1'] != '' and ret['registered_address_town'] == '':
        # This is a workaround for missing town value.
        # Our validation requires town to be present in the company registered address.
        # This is not always the case with Companies House data.
        # It is difficult to tell if registered_address_2 is really a town.
        # Comma put in place of a missing town will satisfy our validation.
        # We assume that registered_address_town with comma is empty.
        ret['registered_address_town'] = ','

    # Nasty... copied from korben
    try:
        ret['incorporation_date'] = datetime.strptime(
            ret['incorporation_date'], '%d/%m/%Y',
        ).date()
    except (TypeError, ValueError):
        ret['incorporation_date'] = None

    # Foreign companies are excluded, so we normalise the country to UK
    ret['registered_address_country_id'] = constants.Country.united_kingdom.value.id

    return ret


@contextmanager
def open_ch_zipped_csv(fp):
    """Enclose all the complicated logic of on-the-fly unzip->csv read in a nice context manager.
    """
    with zipfile.ZipFile(fp) as zf:
        # get the first file from zip, assuming it's the only one from CH
        csv_name = zf.filelist[0].filename
        with zf.open(csv_name) as raw_csv_fp:
            # We need to read that as a text IO for CSV reader to work
            csv_fp = io.TextIOWrapper(raw_csv_fp)

            yield csv.DictReader(csv_fp, fieldnames=CSV_FIELD_NAMES)


def iter_ch_csv_from_url(url, tmp_file_creator):
    """Fetch & cache CH zipped CSV, and then iterate though contents."""
    logger.info('Loading CSV from URL: %s', url)
    with tmp_file_creator() as tf:
        stream_to_file_pointer(url, tf)
        tf.seek(0, 0)

        with open_ch_zipped_csv(tf) as csv_reader:
            next(csv_reader)  # skip the csv header
            for row in csv_reader:
                yield from process_row(row)


def process_row(row):
    """Processes a CH row, yielding a transformed row if the row should be loaded"""
    with sentry_sdk.push_scope() as scope:
        scope.set_extra('record', row)

        if is_relevant_company_type(row):
            yield transform_ch_row(row)


class CHSynchroniser:
    """
    Updates the records in our Companies House table with the latest data from Companies House.

    As this is a large data set (over 4 million records), this is a time-consuming job.

    For speed and as this is a bulk operation, the ORM is not used and native PostgreSQL
    INSERT ... ON CONFLICT (upsert) statements are used instead.

    This is also so the sync can be done without any downtime.
    """

    def __init__(self, simulate=False):
        """Initialises the operation, setting whether database operations should be skipped."""
        self.count = 0
        self.simulate = simulate

    @transaction.atomic
    def run(self, tmp_file_creator, endpoint=None):
        """Runs the synchronisation operation."""
        logger.info('Starting CH load...')
        endpoint = endpoint or settings.COMPANIESHOUSE_DOWNLOAD_URL
        ch_csv_urls = get_ch_latest_dump_file_list(endpoint)
        logger.info('Found the following Companies House CSV URLs: %s', ch_csv_urls)

        for csv_url in ch_csv_urls:
            ch_company_rows = iter_ch_csv_from_url(csv_url, tmp_file_creator)

            batch_iter = slice_iterable_into_chunks(
                ch_company_rows, settings.BULK_INSERT_BATCH_SIZE,
            )
            with connection.cursor() as cursor:
                for batch in batch_iter:
                    self._process_batch(cursor, batch)

        logger.info('Companies House load complete, %s records loaded', self.count)

    def _process_batch(self, cursor, rows):
        if not self.simulate:
            _upsert_ch_records(cursor, rows)

        self.count += len(rows)
        # In debug mode, Django keeps track of SQL statements executed which
        # eventually leads to memory exhaustion.
        # This clears that history.
        reset_queries()

        logger.info('%d Companies House records loaded...', self.count)


def _upsert_ch_records(cursor, rows):
    cursor.executemany(UPSERT_SQL_STATEMENT, rows)


class Command(BaseCommand):
    """Companies House sync command."""

    def add_arguments(self, parser):
        """Define extra arguments."""
        super().add_arguments(parser)
        parser.add_argument(
            '--simulate',
            action='store_true',
            default=False,
            help='If True it only simulates the command without saving the changes.',
        )
        parser.add_argument(
            '--skip-sync-es',
            action='store_true',
            default=False,
            help='Skips running sync_es after the Companies House load finishes.',
        )

    def handle(self, *args, **options):
        """Handle."""
        syncer = CHSynchroniser(simulate=options['simulate'])
        syncer.run(tmp_file_creator=tempfile.TemporaryFile)

        if not options['skip_sync_es']:
            call_command('sync_es', model=['companieshousecompany'])
