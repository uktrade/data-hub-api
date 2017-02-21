"""Various services."""
import csv
import io
import tempfile
import zipfile
from logging import getLogger

import requests
from django.conf import settings
from lxml import etree

from datahub.core.utils import stream_to_fp


logger = getLogger(__name__)


def get_ch_latest_dump_file_list(url, selector='.omega a'):
    """Fetch a list of last published basic data dumps from CH, using a given selector."""
    response = requests.get(url)
    parser = etree.HTMLParser()
    root = etree.parse(io.BytesIO(response.content), parser).getroot()

    result = []
    for anchor in root.cssselect(selector):
        result.append(anchor.attrib['href'])
    return result


def filter_irrelevant_ch_columns(row):
    """Filter out the irrelevant fields from a CH data row."""
    ret = {}
    for name in settings.CH_RELEVANT_FIELDS:
        ret[name] = row.get(name)

    return ret


def open_ch_zipped_csv(fp):
    """Enclose all the complicated logic of on-the-fly unzip->csv read in a nice context manager."""
    with zipfile.ZipFile(fp) as zf:
        # get the first file from zip, assuming it's the only one from CH
        csv_name = zf.filelist[0].filename
        with zf.open(csv_name) as raw_csv_fp:
            # We need to read that as a text IO for CSV reader to work
            csv_fp = io.TextIOWrapper(raw_csv_fp)

            yield csv.DictReader(csv_fp, fieldnames=settings.CH_CSV_FIELD_NAMES)


def iter_ch_csv_from_url(url):
    """Fetch & cache CH zipped CSV, and then iterate though contents."""
    with tempfile.TemporaryFile() as tf:
        logger.info('Downloading: {url}'.format(url=url))
        stream_to_fp(url, tf)
        tf.seek(0, 0)
        logger.info('Downloaded: {url}'.format(url=url))

        with open_ch_zipped_csv(tf) as csv_reader:
            for index, row in enumerate(csv_reader):
                if index == 0:
                    continue  # We're overriding field names, skip header row

                yield filter_irrelevant_ch_columns(row)
