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
from django.db import connection, transaction
from lxml import etree
from raven.contrib.django.raven_compat.models import client

from datahub.company.models import CompaniesHouseCompany
from datahub.core.utils import log_and_ignore_exceptions, slice_iterable_into_chunks, stream_to_file_pointer

logger = getLogger(__name__)


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


def filter_irrelevant_ch_columns(row):
    """Filter out the irrelevant fields from a CH data row and normalize the data."""
    ret = {}
    for name in settings.CH_RELEVANT_FIELDS:
        ret[name] = row.get(name, '')

    # Nasty... copied from korben
    try:
        ret['incorporation_date'] = datetime.strptime(
            ret['incorporation_date'], '%d/%m/%Y'
        ).date()
    except (TypeError, ValueError):
        ret['incorporation_date'] = None

    # bad hacks
    ret['registered_address_country_id'] = settings.CH_UNITED_KINGDOM_COUNTRY_ID

    return ret


@contextmanager
def open_ch_zipped_csv(fp):
    """Enclose all the complicated logic of on-the-fly unzip->csv read in a nice context manager."""
    with zipfile.ZipFile(fp) as zf:
        # get the first file from zip, assuming it's the only one from CH
        csv_name = zf.filelist[0].filename
        with zf.open(csv_name) as raw_csv_fp:
            # We need to read that as a text IO for CSV reader to work
            csv_fp = io.TextIOWrapper(raw_csv_fp)

            yield csv.DictReader(csv_fp, fieldnames=settings.CH_CSV_FIELD_NAMES)


def iter_ch_csv_from_url(url, tmp_file_creator):
    """Fetch & cache CH zipped CSV, and then iterate though contents."""
    with tmp_file_creator() as tf:
        stream_to_file_pointer(url, tf)
        tf.seek(0, 0)

        with open_ch_zipped_csv(tf) as csv_reader:
            next(csv_reader)  # skip the csv header
            for row in csv_reader:
                yield filter_irrelevant_ch_columns(row)


def sync_ch(tmp_file_creator, endpoint=None, truncate_first=False):
    """Do the sync.

    We are batching the records instead of letting bulk_create doing it because Django casts the objects into a list
    https://github.com/django/django/blob/master/django/db/models/query.py#L420
    this would create a list with millions of objects, that will try to be saved in batches in a single transaction
    """
    endpoint = endpoint or settings.CH_DOWNLOAD_URL
    ch_csv_urls = get_ch_latest_dump_file_list(endpoint)
    if truncate_first:
        truncate_ch_companies_table()
    for csv_url in ch_csv_urls:
        ch_company_rows = iter_ch_csv_from_url(csv_url, tmp_file_creator)
        for batchiter in slice_iterable_into_chunks(ch_company_rows, settings.BULK_CREATE_BATCH_SIZE):
            objects = [CompaniesHouseCompany(**ch_company_row) for ch_company_row in batchiter if ch_company_row]
            CompaniesHouseCompany.objects.bulk_create(
                objs=objects,
                batch_size=settings.BULK_CREATE_BATCH_SIZE
            )


@transaction.atomic
def truncate_ch_companies_table():
    """Delete all the companies house companies.

    delete() is too slow, we use truncate.
    """
    cursor = connection.cursor()
    table_name = CompaniesHouseCompany._meta.db_table
    query = f'truncate {table_name};'
    cursor.execute(query)


class Command(BaseCommand):
    """Companies House sync command."""

    def handle(self, *args, **options):
        """Handle."""
        try:
            sync_ch(tmp_file_creator=tempfile.TemporaryFile, truncate_first=True)
        except Exception as e:
            with log_and_ignore_exceptions():
                client.captureException()

            logger.exception('Failed to sync from ES')
            self.stderr.write(e)
