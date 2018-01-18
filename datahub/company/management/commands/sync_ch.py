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
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries, transaction
from lxml import etree
from raven.contrib.django.raven_compat.models import client

from datahub.company.models import CompaniesHouseCompany
from datahub.core.utils import slice_iterable_into_chunks, stream_to_file_pointer

logger = getLogger(__name__)

# Mapping used by is_relevant_company_type() to determine which companies should be loaded
COMPANY_CATEGORY_RELEVANCY_MAPPING = {
    'community interest company': True,
    'european public limited-liability company (se)': True,
    # Address not available/main registration with FCA
    'industrial and provident society': False,
    # Address not available/main registration with FCA
    'investment company with variable capital': False,
    # Address not available/main registration with FCA
    'investment company with variable capital (securities)': False,
    # Address not available/main registration with FCA
    'investment company with variable capital(umbrella)': False,
    'limited liability partnership': True,
    'limited partnership': True,
    'old public company': True,
    # Foreign and other irrelevant companies
    'other company type': False,
    "pri/lbg/nsc (private, limited by guarantee, no share capital, use of 'limited' exemption)":
        True,
    'pri/ltd by guar/nsc (private, limited by guarantee, no share capital)': True,
    'priv ltd sect. 30 (private limited company, section 30 of the companies act)': True,
    'private limited company': True,
    'private unlimited': True,
    'private unlimited company': True,
    # Address not available/main registration with FCA
    'protected cell company': False,
    'public limited company': True,
    # Address not available/main registration with FCA
    'registered society': False,
    # Address not available
    'royal charter company': False,
    # Scottish qualifying partnership, generally have a foreign address
    'scottish partnership': False,
}


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
    is_relevant = COMPANY_CATEGORY_RELEVANCY_MAPPING.get(row['company_category'].lower())
    if is_relevant is None:
        message = (f'Unknown Companies House company category {row["company_category"]} '
                   f'encountered. Update the company category relevancy mapping to indicate if '
                   f'it should be loaded.')
        logger.warning(message)
        client.captureMessage(message)
    return is_relevant


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
    for name in settings.CH_RELEVANT_FIELDS:
        ret[name] = row.get(name, '')

    if 'registered_address_town' in row and row['registered_address_town'] == '':
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
            ret['incorporation_date'], '%d/%m/%Y'
        ).date()
    except (TypeError, ValueError):
        ret['incorporation_date'] = None

    # Foreign companies are excluded, so we normalise the country to UK
    ret['registered_address_country_id'] = settings.CH_UNITED_KINGDOM_COUNTRY_ID

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

            yield csv.DictReader(csv_fp, fieldnames=settings.CH_CSV_FIELD_NAMES)


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
    with client.context:
        client.context.merge({'record': row})

        if is_relevant_company_type(row):
            yield transform_ch_row(row)


def sync_ch(tmp_file_creator, endpoint=None, truncate_first=False, simulate=False):
    """Do the sync.

    We are batching the records instead of letting bulk_create doing it because Django casts
    the objects into a list:
    https://github.com/django/django/blob/master/django/db/models/query.py#L420

    This would create a list with millions of objects, that will try to be saved in batches
    in a single transaction.
    """
    logger.info('Starting CH load...')
    count = 0
    endpoint = endpoint or settings.CH_DOWNLOAD_URL
    ch_csv_urls = get_ch_latest_dump_file_list(endpoint)
    logger.info('Found the following Companies House CSV URLs: %s', ch_csv_urls)
    if truncate_first and not simulate:
        truncate_ch_companies_table()
    for csv_url in ch_csv_urls:
        ch_company_rows = iter_ch_csv_from_url(csv_url, tmp_file_creator)

        batch_iter = slice_iterable_into_chunks(
            ch_company_rows, settings.BULK_CREATE_BATCH_SIZE, _create_ch_company
        )
        for batch in batch_iter:
            if not simulate:
                CompaniesHouseCompany.objects.bulk_create(
                    objs=batch,
                    batch_size=settings.BULK_CREATE_BATCH_SIZE
                )
            count += len(batch)
            logger.info('%d Companies House records loaded...', count)
            # In debug mode, Django keeps track of SQL statements executed which
            # eventually leads to memory exhaustion.
            # This clears that history.
            reset_queries()

    logger.info('Companies House load complete, %s records loaded', count)


@transaction.atomic
def truncate_ch_companies_table():
    """Delete all the companies house companies.

    delete() is too slow, we use truncate.
    """
    cursor = connection.cursor()
    table_name = CompaniesHouseCompany._meta.db_table
    logger.info('Truncating the %s table', table_name)
    query = f'truncate {table_name};'
    cursor.execute(query)


def _create_ch_company(row_dict):
    return CompaniesHouseCompany(**row_dict)


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

    def handle(self, *args, **options):
        """Handle."""
        sync_ch(
            tmp_file_creator=tempfile.TemporaryFile,
            truncate_first=True,
            simulate=options['simulate'],
        )
