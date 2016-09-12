from .. import db


def from_cdms_psql(metadata, entity_name, data):
    table = metadata.tables[entity_name]
    return metadata.bind.connect().execute(table.insert(), data)

def from_ch(metadata, data):
    table = metadata.tables['api_chcompany']
    return metadata.bind.connect().execute(table.insert(), data)
