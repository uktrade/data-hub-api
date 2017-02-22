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
from lxml import etree
from raven.contrib.django.raven_compat.models import client

from datahub.company.models import CompaniesHouseCompany
from datahub.core.utils import log_and_ignore_exceptions, stream_to_file_pointer

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
        result.append('{0.scheme}://{0.hostname}/{1}'.format(url_base, href))
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
        pass

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
        logger.info('Downloading: {url}'.format(url=url))
        stream_to_file_pointer(url, tf)
        tf.seek(0, 0)
        logger.info('Downloaded: {url}'.format(url=url))

        with open_ch_zipped_csv(tf) as csv_reader:
            for index, row in enumerate(csv_reader):
                if index == 0:
                    continue  # We're overriding field names, skip header row

                yield filter_irrelevant_ch_columns(row)


def is_changed(company, csv_data):
    """Return whatever company data changed."""
    return any(csv_data[name] != getattr(company, name) for name in csv_data)


def sync_ch(tmp_file_creator, endpoint=None):
    """Do the sync."""
    endpoint = endpoint or settings.CH_DOWNLOAD_URL
    ch_csv_urls = get_ch_latest_dump_file_list(endpoint)

    for csv_url in ch_csv_urls:
        for ch_company_row in iter_ch_csv_from_url(csv_url, tmp_file_creator):
            company, created = CompaniesHouseCompany.objects.get_or_create(
                company_number=ch_company_row.pop('company_number'),
                defaults=ch_company_row,
            )

            if created or not is_changed(company, ch_company_row):
                continue

            for key, value in ch_company_row.items():
                setattr(company, key, value)

            company.save()


class Command(BaseCommand):
    """Companies House sync command."""

    def handle(self, *args, **options):
        """Handle."""
        try:
            sync_ch(tmp_file_creator=tempfile.TemporaryFile)
        except Exception as e:
            with log_and_ignore_exceptions():
                client.captureException()

            logger.exception('Failed to sync from ES')
            self.stderr.write(e)
