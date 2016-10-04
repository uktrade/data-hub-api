import datetime
import itertools
import logging
import os
import re

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import exc as sqla_exc

from korben import config
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
    for row in data:
        upsert = insert(table)\
            .values(**row)\
            .on_conflict_do_update(index_elements=[primary_key], set_=row)
        results.append(table.metadata.bind.execute(upsert))
        '''
        try:
            results.append(table.metadata.bind.execute(upsert))
        except sqla_exc.IntegrityError as exc:
            parsed = re.search(INTEGRITY_DETAILS, str(exc))
            with open('cache/fails', 'a') as fails_fh:
                fails_fh.write(
                    "{0}, {1}\n".format(
                        parsed.group('pkey'), parsed.group('table')
                    )
                )
        except Exception as exc:
            LOGGER.error(exc)
            LOGGER.error("{0} {1} ({2}) failed on something".format(
                datetime.datetime.now(), table.name, row[primary_key]
            ))
            pass
        '''
    return results


def from_ch(data):
    metadata = services.db.poll_for_metadata(config.database_url)
    table = metadata.tables['company_companieshousecompany']
    return metadata.bind.connect().execute(table.insert(), data)
