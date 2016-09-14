from sqlalchemy.dialects.postgresql import insert

from korben import config
from .. import services


def to_cdms_psql(entity_name, data):
    'Load data into a cdms_psql table'
    metadata = services.db.poll_for_metadata(config.database_odata_url)
    table = metadata.tables[entity_name + 'Set']
    return metadata.bind.connect().execute(table.insert(), data)


def to_leeloo(name, data):
    'Load data into a cdms_psql table'
    metadata = services.db.poll_for_metadata(config.database_url)
    table = metadata.tables[name]
    return metadata.bind.execute(table.insert().values(list(data)))


def to_leeloo_idempotent(name, data):
    'Idempotently load data into a cdms_psql table'
    metadata = services.db.poll_for_metadata(config.database_url)
    table = metadata.tables[name]
    primary_key = next(
        col.name for col in table.primary_key.columns.values()
    )
    results = []
    for row in data:
        upsert = insert(table)\
            .values(**row)\
            .on_conflict_do_update(index_elements=[primary_key], set_=row)
        results.append(metadata.bind.execute(upsert))
    return results


def from_ch(data):
    metadata = services.db.poll_for_metadata(config.database_url)
    table = metadata.tables['api_chcompany']
    return metadata.bind.connect().execute(table.insert(), data)
