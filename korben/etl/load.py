import collections
import datetime
import itertools
import logging
import os
import re

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import exc as sqla_exc

from korben import etl
from .. import services

LOGGER = logging.getLogger('korben.etl.load')
INTEGRITY_DETAILS = re.compile('(\(.+\))=\((?P<pkey>.+)\).+"(?P<table>.+)"')


def to_sqla_table(table, data):
    'Load data into an SQLA table'
    results = []
    for chunk in itertools.zip_longest(*[iter(data)] * 5000):
        results.append(
            table.metadata.bind.execute(
                table.insert().values(list(filter(None, chunk)))
            )
        )
    return results


def to_sqla_table_idempotent(table, data):
    '''
    Idempotently load data into an SQLA table, temporarily write out details on
    integrity errors to a file
    '''
    primary_key = etl.utils.primary_key(table)
    results = []
    missing = collections.defaultdict(set)
    for row in data:
        upsert = insert(table)\
            .values(**row)\
            .on_conflict_do_update(index_elements=[primary_key], set_=row)
        try:
            results.append(table.metadata.bind.execute(upsert))
        except sqla_exc.IntegrityError as exc:
            parsed = re.search(INTEGRITY_DETAILS, str(exc))
            if parsed:
                missing[table.name].add(row[primary_key])
                missing[parsed.group('table')].add(parsed.group('pkey'))
                continue
            LOGGER.error(
                '%s %s (%s) failed on :',
                datetime.datetime.now(), table.name, row[primary_key]
            )
            LOGGER.error(str(exc).split('\n')[0])
    return results, missing


def from_ch(data):
    metadata = services.db.get_django_metadata()
    table = metadata.tables['company_companieshousecompany']
    return metadata.bind.connect().execute(table.insert(), data)
