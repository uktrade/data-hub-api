from sqlalchemy.dialects.postgresql import insert

from korben import config
from .. import services


def to_cdms_psql(table, data):
    'Load data into a cdms_psql table'
    return table.metadata.bind.connect().execute(table.insert(), data)


def to_leeloo(table, data):
    'Load data into a cdms_psql table'
    return table.metadata.bind.execute(table.insert().values(list(data)))


def to_leeloo_idempotent(table, data):
    'Idempotently load data into a cdms_psql table'
    primary_key = next(
        col.name for col in table.primary_key.columns.values()
    )
    results = []
    for row in data:
        upsert = insert(table)\
            .values(**row)\
            .on_conflict_do_update(index_elements=[primary_key], set_=row)
        results.append(table.metadata.bind.execute(upsert))
    return results


def from_ch(data):
    metadata = services.db.poll_for_metadata(config.database_url)
    table = metadata.tables['company_companyhousecompany']
    return metadata.bind.connect().execute(table.insert(), data)
