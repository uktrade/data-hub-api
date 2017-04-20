import sqlalchemy as sqla
from . import utils


def from_odata(table, guids):
    select_statement = (
        sqla
        .select([table])
        .where(table.columns[utils.primary_key(table)].in_(guids))
    )
    result = table.metadata.bind.connect().execute(select_statement).fetchall()
    return map(dict, result)
