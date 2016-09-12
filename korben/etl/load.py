from korben import config
from .. import db


def to_cdms_psql(entity_name, data):
    'Load data into a cdms_psql table'
    metadata = db.poll_for_metadata(config.database_odata_url)
    table = metadata.tables[entity_name + 'Set']
    return metadata.bind.connect().execute(table.insert(), data)


def to_leeloo(name, data):
    'Load data into a cdms_psql table'
    metadata = db.poll_for_metadata(config.database_url)
    table = metadata.tables[name]
    return metadata.bind.execute(table.insert().values(list(data)))


def from_ch(data):
    metadata = db.poll_for_metadata(config.database_url)
    table = metadata.tables['api_chcompany']
    return metadata.bind.connect().execute(table.insert(), data)
